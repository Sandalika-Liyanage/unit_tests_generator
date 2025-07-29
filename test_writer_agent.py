import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4", temperature=0.1)

def test_writer_node(state):
    """Writes test code for a single scenario using LLM"""
    print("Agent: Test Writer")

    scenarios = state["test_scenarios"]
    current_index = state.get("current_scenario_index", 0)
    
    if current_index >= len(scenarios):
        return state
    
    current_scenario = scenarios[current_index]
    print(f"Writing test {current_index + 1}/{len(scenarios)}: {current_scenario.get('test_name', 'Unknown')}")
    
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
        print(f"Test generated successfully")
        
    except Exception as e:
        print(f"Error generating test code: {e}")
        updated_tests = state["generated_tests"]
    
    return {
        **state,
        "generated_tests": updated_tests,
        "current_scenario_index": current_index + 1
    }