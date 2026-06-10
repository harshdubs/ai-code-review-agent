import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from state import AgentState
import requests
import time

load_dotenv()

llm = ChatOpenAI(
    api_key=os.environ.get("NVIDIA_API_KEY"),
    base_url="https://integrate.api.nvidia.com/v1",
    model="meta/llama-3.1-70b-instruct",
    temperature=0
)

llm_fast = ChatGroq(
    api_key=os.environ.get("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",
    temperature=0
)

def truncate_code(code: str, max_chars: int = 4000) -> str:
    if len(code) > max_chars:
        return code[:max_chars] + "\n... [truncated for processing]"
    return code

def invoke_with_retry(llm, prompt, retries=5, wait=10):
    for attempt in range(retries):
        try:
            return llm.invoke(prompt)
        except Exception as e:
            if "rate_limit" in str(e).lower() or "429" in str(e):
                time.sleep(wait)
            else:
                raise e
    raise Exception("Max retries exceeded")

def fetch_code(state: AgentState):
    code_input = state['code_input']

    if code_input.startswith("https://github.com"):
        code_input = code_input.replace("github.com","raw.githubusercontent.com").replace("/blob/","/")
        response = requests.get(code_input)
        code = response.text
    else:
        code = code_input
    
    return {"raw_code": truncate_code(code)}


def bug_reviewer(state: AgentState):
    print(">>bug reviewer running...")
    response = invoke_with_retry(llm_fast, f"""Review the following code for bugs, logic errors, unhandled exceptions, 
        off-by-one errors, null/undefined checks, and incorrect conditions. 
        For each bug found, explain what it is, why it's a problem, and suggest 
        a specific fix. Format as numbered list. Code: {state["raw_code"]}""")  
    return {"bug_review" : response.content}

def security_reviewer(state: AgentState):
    print("security reviewer running....")
    response = invoke_with_retry(llm_fast, f"""Review the following code for security vulnerabilities including SQL injection, 
        hardcoded secrets or API keys, unvalidated user inputs, insecure dependencies, 
        exposed sensitive data, and authentication issues. For each vulnerability found, 
        rate its severity (High/Medium/Low), explain the risk, and suggest a fix. 
        Format as numbered list. Code: {state["raw_code"]}""")
    return {"security_review" : response.content}

def performance_reviewer(state: AgentState):
    print("performance reviewer running....")
    response = invoke_with_retry(llm_fast, f"""Review the following code for performance issues including unnecessary loops, 
        inefficient data structures, redundant API or database calls, memory leaks, 
        blocking operations, and algorithmic complexity issues. For each issue found, 
        explain the impact and suggest an optimized approach. 
        Format as numbered list. Code: {state["raw_code"]}""")
    return {"performance_review" : response.content}

def report_generator(state: AgentState):
    print("report generator running.....")
    response = invoke_with_retry(llm_fast, f"""Generate a comprehensive code review report by combining the following three reviews.
        Structure the report with clear sections: Executive Summary, Bug Analysis, Security Analysis, 
        Performance Analysis, and Overall Recommendations. Prioritize critical issues at the top.

        Bug Review: {state["bug_review"]}
        Security Review: {state["security_review"]}  
        Performance Review: {state["performance_review"]}""")
    return {"final_report" : response.content}

def code_fixer(state: AgentState):
    print("code fixer  running ........")
    truncated_report = truncate_code(state["final_report"], max_chars=1000)
    response = invoke_with_retry(llm_fast, f"""You are fixing the code below. 
        Do NOT rewrite it from scratch. 
        Do NOT replace it with different code.
        ONLY fix the specific issues mentioned in the review.
        Return the SAME code with ONLY the identified issues fixed.

        Original Code:
        {state["raw_code"]}
        
        Issues to fix:
        {truncated_report}""")
    return {"fixed_code": response.content}

def verify_fix(state: AgentState):
    print("verifying fix right now.......")
    current_count = state.get("iteration_count", 0)
    truncated = truncate_code(state["fixed_code"], max_chars=1500)
    response = invoke_with_retry(llm_fast, f"""Review this fixed code and determine if any critical issues remain.
        Be strict. Check for bugs, security issues, and performance problems.
        At the very end of your response, on a new line, write exactly one of:
        ISSUES_FOUND
        NO_ISSUES

        Fixed Code: {truncated}""")
    return {"verify_output": response.content, "iteration_count": current_count + 1}

def test_generator(state: AgentState):
    print(" test generator running.......")
    response = invoke_with_retry(llm_fast, f"""Generate comprehensive unit tests for the following code. 
        Cover normal cases, edge cases, and error cases. 
        Use pytest format.

        Code: {state["fixed_code"]}""")
    return {"test_cases": response.content}

