import tempfile
import json
import os
import subprocess
from typing import Dict, List, Any
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4", temperature=0.1)

class TestVerificationResult:
    def __init__(self):
        self.build_passed = False
        self.tests_passed = False
        self.coverage_percentage = 0.0
        self.build_errors = []
        self.test_failures = []
        self.coverage_report = {}
        self.suggestions = []
        
def verification_agent_node(state):
    """Verification agent that validates generated tests through multiple checks"""
    print("Agent : Test verification")

    if not state.get("generated_tests"):
        print("No tests to verify")
        return {**state, "verfication_results":[]}
    
    verification_results = []

    #go though each generated test and print a progress message-> for ...in ... :this starts a loop that will repeat for every item in a list,
    #state["generated_tests"]: this is the list of generated tests code strings that the loop iterate over
    #enumerate(..., 1)This is the counter to the loop
    for i, test_code in enumerate(state["generated_tests"]):
        print(f"Verifying test {i+1}/{len(state['generated_tests'])}")

        result=TestVerificationResult()

        #step 1:Build/Syntax check
        #calling the helper fucntion(_builder_check)
        # we pass three things to it,test_code(code for a single unit test that it wants to check), 
        # state["source_code"](original source code , that the test is for) and result
        result=_build_check(test_code, state["source_code"], result)

        if result.build_passed:
            #step 2: pass check (only if build passes)
            result=_pass_check(test_code, state["source_code"], state["file_path"])

            if result.tests_passed:
                #step 3: coverage check (only if pass tests pass)
                result=_coverage_check(test_code, state["source_code"], state["file_path"], result)

        #step 4: generate suggestions for improvements
        result=_generate_suggestions(test_code, state["source_code"], result)

        verification_results.append({
            "test_index": i,
            "build_passed":result.build_passed,
            "tests_passed":result.tests_passed,
            "coverage_percentage":result.coverage_percentage,
            "build_errors":result.build_errors,
            "test_failures":result.test_failures,
            "coverage_report":result.coverage_report,
            "suggestions":result.suggestions,
           
        })

    return {**state, "verfication_results":verification_results}