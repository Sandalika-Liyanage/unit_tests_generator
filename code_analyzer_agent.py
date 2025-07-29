import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
import os
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4", temperature=0.1)

@tool
def read_source_file(file_path: str) -> str:
    """Read the full content of a specified source code file."""
    print(f"Reading file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: The file at path '{file_path}' was not found."
    except UnicodeDecodeError:
        return f"Error: Could not decode file at path '{file_path}'. File may be binary."

def code_analyser_node(state):
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
        print(f"Found {len(code_map.get('functions', []))} functions and {len(code_map.get('classes', []))} classes")
        
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error parsing LLM response: {e}")
        code_map = {
            "functions": [],
            "classes": [],
            "imports": [],
            "overall_complexity": "unknown"
        }
    
    return {**state, "source_code": source_code, "code_map": code_map}