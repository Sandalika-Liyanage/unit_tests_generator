import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4", temperature=0.1)

def test_strategist_node(state):
    """Creates a filtered test plan using the LLM"""
    print("Agent: Test Strategist")
    
    if not state.get("execution_paths"):
        print("No execution paths to create test scenarios")
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
        
        print(f"Created {len(test_scenarios)} test scenarios")
        
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error parsing test scenarios: {e}")
        test_scenarios = []
    
    return {
        **state,
        "test_scenarios": test_scenarios, 
        "generated_tests": [],
        "current_scenario_index": 0
    }