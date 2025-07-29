import glob
import json
from typing import List, Dict, Any, TypedDict, Optional
from dotenv import load_dotenv
load_dotenv()

# LangChain / LangGraph imports
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
import os

# Set OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4", temperature=0.1)

# --- State Definition ---
class TestGenerationState(TypedDict):
    file_path: str
    source_code: Optional[str] 
    code_map: Dict[str, Any]
    execution_paths: Dict[str, Any]
    test_scenarios: List[Dict[str, Any]]
    generated_tests: List[str]
    current_scenario_index: int

# --- Tool Definition ---
@tool
def read_source_file(file_path: str) -> str:
    """Read the full content of a specified source code file."""
    print(f"📖 Reading file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: The file at path '{file_path}' was not found."
    except UnicodeDecodeError:
        return f"Error: Could not decode file at path '{file_path}'. File may be binary."

# --- Agent 1: Code Analyzer ---
def code_analyser_node(state: TestGenerationState) -> TestGenerationState:
    """Agent that reads and analyzes the source code using LLM."""
    print("🔍 Agent: Code Analyzer")
    
    source_code = read_source_file.invoke({"file_path": state["file_path"]})
    if source_code.startswith("Error:"):
        return {**state, "source_code": source_code, "code_map": {}}

    system_prompt = """You are a Python code analyzer. Analyze the given source code and extract:
1. All functions (including class methods and static methods) with their signatures
2. All classes and their methods  
3. Key imports and dependencies
4. Main code complexity and structure

Return ONLY a valid JSON object with this structure:
{
    "functions": [
        {
            "name": "function_name or ClassName.method_name",
            "params": ["param1", "param2"],
            "return_type": "return_type_hint_or_inferred",
            "complexity": "simple|medium|complex",
            "description": "brief description of what it does"
        }
    ],
    "classes": [
        {
            "name": "ClassName", 
            "methods": ["method1", "method2"],
            "description": "brief description"
        }
    ],
    "imports": ["import1", "import2"],
    "overall_complexity": "simple|medium|complex"
}"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Analyze this Python code:\n\n```python\n{source_code}\n```")
    ]

    try: 
        response = llm.invoke(messages)
        response_text = response.content.strip()

        # Extract JSON from response
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        else:
            json_text = response_text
        
        code_map = json.loads(json_text)
        print(f"   ✅ Found {len(code_map.get('functions', []))} functions and {len(code_map.get('classes', []))} classes")
        
    except (json.JSONDecodeError, Exception) as e:
        print(f"   ❌ Error parsing LLM response: {e}")
        code_map = {
            "functions": [],
            "classes": [],
            "imports": [],
            "overall_complexity": "unknown"
        }
    
    return {**state, "source_code": source_code, "code_map": code_map}

# --- Agent 2: Function Path Agent ---
def function_path_node(state: TestGenerationState) -> TestGenerationState:
    """Maps out all possible execution paths using LLM."""
    print("🛤️  Agent: Function Path")

    if not state["code_map"] or not state["code_map"].get("functions"):
        print("   ⚠️  No functions found to analyze paths")
        return {**state, "execution_paths": {}}
    
    system_prompt = """You are a test path analyzer. For each function in the code, identify all possible execution paths:
1. Happy path (normal successful execution)
2. Edge cases (boundary conditions, empty inputs, etc.)
3. Error cases (invalid inputs, exceptions)
4. Special conditions (None values, type mismatches, etc.)

Return ONLY a valid JSON object mapping function names to their execution paths:
{
    "function_name": [
        {
            "path_type": "happy_path|edge_case|error_case",
            "description": "description of this path",
            "test_inputs": "example inputs for this path",
            "expected_behavior": "what should happen"
        }
    ]
}"""

    functions_info = json.dumps(state["code_map"]["functions"], indent=2)
    source_code = state["source_code"][:2000] if state["source_code"] else ""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Functions to analyze:\n{functions_info}\n\nSource code snippet:\n```python\n{source_code}\n```")
    ]

    try:
        response = llm.invoke(messages)
        response_text = response.content.strip()
        
        # Extract JSON from response
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        else:
            json_text = response_text
        
        execution_paths = json.loads(json_text)
        print(f"   ✅ Mapped execution paths for {len(execution_paths)} functions")
        
    except (json.JSONDecodeError, Exception) as e:
        print(f"   ❌ Error parsing execution paths: {e}")
        execution_paths = {}
    
    return {**state, "execution_paths": execution_paths}

# --- Agent 3: Test Strategist Agent ---
def test_strategist_node(state: TestGenerationState) -> TestGenerationState:
    """Creates a filtered test plan using the LLM"""
    print("🎯 Agent: Test Strategist")
    
    if not state.get("execution_paths"):
        print("   ⚠️  No execution paths to create test scenarios")
        return {**state, "test_scenarios": [], "generated_tests": [], "current_scenario_index": 0}

    system_prompt = """You are a test strategist. Based on the code analysis and execution paths, create a comprehensive test plan.
Prioritize:
1. Critical functionality tests
2. Edge cases that are likely to break  
3. Error handling tests
4. Integration points

Return ONLY a valid JSON array of test scenarios:
[
    {
        "function": "function_name",
        "test_name": "descriptive_test_name", 
        "description": "what this test validates",
        "priority": "high|medium|low",
        "test_type": "unit|integration|edge_case|error_handling",
        "setup_required": "any setup needed",
        "test_inputs": "specific inputs to use",
        "expected_output": "expected result or behavior"
    }
]"""

    context = {
        "functions": state["code_map"].get("functions", []),
        "execution_paths": state["execution_paths"]
    }
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Create test scenarios for:\n{json.dumps(context, indent=2)}")
    ]
    
    try:
        response = llm.invoke(messages)
        response_text = response.content.strip()
        
        # Extract JSON from response
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        else:
            json_text = response_text
        
        test_scenarios = json.loads(json_text)
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        test_scenarios.sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 1))
        
        print(f"   ✅ Created {len(test_scenarios)} test scenarios")
        
    except (json.JSONDecodeError, Exception) as e:
        print(f"   ❌ Error parsing test scenarios: {e}")
        test_scenarios = []
    
    return {
        **state,
        "test_scenarios": test_scenarios, 
        "generated_tests": [],
        "current_scenario_index": 0
    }

# --- Agent 4: Test Writer Agent ---
def test_writer_node(state: TestGenerationState) -> TestGenerationState:
    """Writes test code for a single scenario using LLM"""
    print("✍️  Agent: Test Writer")

    scenarios = state["test_scenarios"]
    current_index = state.get("current_scenario_index", 0)
    
    if current_index >= len(scenarios):
        return state
    
    current_scenario = scenarios[current_index]
    print(f"   📝 Writing test {current_index + 1}/{len(scenarios)}: {current_scenario.get('test_name', 'Unknown')}")
    
    system_prompt = """You are a Python test code writer. Write a complete, executable pytest test function based on the scenario.

Requirements:
1. Use pytest conventions
2. Include proper imports at the top
3. Add descriptive docstrings
4. Use appropriate assertions
5. Handle setup/teardown if needed
6. Include edge case validation
7. Use proper mocking if external dependencies are involved

Return ONLY the complete test code, no explanations."""

    # Include relevant source code context
    source_snippet = state["source_code"][:1500] if state["source_code"] else ""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"""Write a test for this scenario:
{json.dumps(current_scenario, indent=2)}

Source code context:
```python
{source_snippet}
```

Generate complete test code with all necessary imports.""")
    ]
    
    try:
        response = llm.invoke(messages)
        generated_code = response.content
        
        # Clean up the response to extract just the Python code
        if "```python" in generated_code:
            code_start = generated_code.find("```python") + 9
            code_end = generated_code.find("```", code_start)
            generated_code = generated_code[code_start:code_end].strip()
        elif "```" in generated_code:
            code_start = generated_code.find("```") + 3
            code_end = generated_code.find("```", code_start)
            generated_code = generated_code[code_start:code_end].strip()
        
        # Add test to the list
        updated_tests = state["generated_tests"] + [generated_code]
        print(f"   ✅ Test generated successfully")
        
    except Exception as e:
        print(f"   ❌ Error generating test code: {e}")
        updated_tests = state["generated_tests"]
    
    return {
        **state,
        "generated_tests": updated_tests,
        "current_scenario_index": current_index + 1
    }

# --- Conditional Logic ---
def should_continue_writing(state: TestGenerationState) -> str:
    """Determines whether to continue writing tests"""
    current_index = state.get("current_scenario_index", 0)
    total_scenarios = len(state.get("test_scenarios", []))
    
    if current_index < total_scenarios:
        return "continue"
    else:
        print("   🎉 All tests generated!")
        return "end"

# --- Graph Construction ---
workflow = StateGraph(TestGenerationState)

# Add nodes (agents)
workflow.add_node("code_analyser", code_analyser_node)
workflow.add_node("function_path", function_path_node) 
workflow.add_node("test_strategist", test_strategist_node)
workflow.add_node("test_writer", test_writer_node)

# Set entry point
workflow.set_entry_point("code_analyser")

# Add edges (flow)
workflow.add_edge("code_analyser", "function_path")
workflow.add_edge("function_path", "test_strategist") 
workflow.add_conditional_edges(
    "test_strategist",
    should_continue_writing,
    {"continue": "test_writer", "end": END}
)
workflow.add_conditional_edges(
    "test_writer", 
    should_continue_writing,
    {"continue": "test_writer", "end": END}
)

# Compile the workflow
app = workflow.compile()

# --- Main Execution Logic ---
if __name__ == "__main__":
    # Configuration
    repo_path = "app"  # Path relative to the script's location
    output_dir = "generated_tests"
    
    # Validate API key
    if not OPENAI_API_KEY :
        print("❌ Please set your OpenAI API key!")
        print("Either set the OPENAI_API_KEY environment variable or update the .env file.")
        exit(1)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Find all Python files
    source_files = glob.glob(f"{repo_path}/**/*.py", recursive=True)
    
    # Filter out test files and __pycache__
    source_files = [f for f in source_files if not f.endswith('test.py') 
                and 'test_' not in os.path.basename(f)
                and '__pycache__' not in f
                and '__init__.py' not in f]  # Skip __init__.py files

    if not source_files:
        print(f"No Python files found in {repo_path}. Please check the path.")
        exit(1)
    
    print(f"🚀 Found {len(source_files)} Python files to test.\n")
    
    # Process each file
    for i, file_path in enumerate(source_files, 1):
        print(f"\n{'='*60}")
        print(f"📁 Processing file {i}/{len(source_files)}: {file_path}")
        print(f"{'='*60}")
        
        # Initialize state
        inputs = {
            "file_path": file_path,
            "source_code": None,
            "code_map": {},
            "execution_paths": {},
            "test_scenarios": [],
            "generated_tests": [],
            "current_scenario_index": 0
        }
        
        try:
            # Run the workflow
            result = app.invoke(inputs)
            
            # Save generated tests
            if result.get("generated_tests"):
                base_name = os.path.basename(file_path).replace('.py', '')
                output_file_path = os.path.join(output_dir, f"test_{base_name}.py")
                
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.write("# Auto-generated tests using AI-powered multi-agent analysis\n")
                    f.write(f"# Source file: {file_path}\n")
                    f.write("# Generated by LangGraph Test Generator\n\n")
                    f.write("import pytest\n")
                    f.write("from unittest.mock import Mock, patch\n\n")
                    
                    for j, test_code in enumerate(result["generated_tests"], 1):
                        f.write(f"# Test {j}\n")
                        f.write(test_code)
                        f.write("\n\n")
                
                print(f"💾 Generated {len(result['generated_tests'])} tests saved to {output_file_path}")
            else:
                print(f"⚠️  No tests generated for {file_path}")
                
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            continue
    
    print(f"\n🎉 Test generation completed! Check the '{output_dir}' directory for results.")