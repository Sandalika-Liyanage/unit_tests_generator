import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4", temperature=0.1)

def function_path_node(state):
    """Maps out all possible execution paths using LLM."""
    print("Agent: Function Path")

    if not state["code_map"] or not state["code_map"].get("functions"):
        print("No functions found to analyze paths")
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
        print(f"Mapped execution paths for {len(execution_paths)} functions")
        
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error parsing execution paths: {e}")
        execution_paths = {}
    
    return {**state, "execution_paths": execution_paths}