import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from state import AgentState
import requests
import time

load_dotenv()

llm = ChatOpenAI(
    api_key=os.environ.get("CEREBRAS_API_KEY"),
    base_url="https://api.cerebras.ai/v1",
    model="gpt-oss-120b",
    temperature=0,
    max_retries=0
)

llm_2 = ChatGroq(
    api_key=os.environ.get("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",
    temperature=0
)

def log_time(label, start_time):
    elapsed = time.time() - start_time
    print(f">>> {label} took {elapsed:.2f}s")

def truncate_code(code: str, max_chars: int = 4000) -> str:
    if len(code) > max_chars:
        return code[:max_chars] + "\n... [truncated for processing]"
    return code

def invoke_with_retry(llm, prompt, retries=6, wait=10):
    for attempt in range(retries):
        try:
            return llm.invoke(prompt)
        except Exception as e:
            print(f">>> RETRY TRIGGERED: {str(e)[:300]}")
            if "429" in str(e) or "rate_limit" in str(e).lower() or "quota" in str(e).lower():
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

def code_writer(state: AgentState):
    start = time.time()
    description = state['user_description']
    response = invoke_with_retry(llm, f"""You are an expert software engineer. Write clean, complete, working code based on this description.

        Requirements:
        - Write production-quality code with proper error handling
        - Include clear comments explaining key logic
        - Use a clear, commonly-used language appropriate for the task (default to Python unless the description specifies otherwise)
        - Return ONLY the code itself, no explanations, no markdown formatting, no code fences
        - Make sure the code is complete and runnable, not a snippet or pseudocode

        Description: {state['user_description']}""" )
    log_time("code writer:", start)
    return {"raw_code": response.content}


def bug_reviewer_r1(state: AgentState):
    start = time.time()
    context = state.get("code_context", "")
    context_note = f"Context about this code: {context}\n" if context else ""
    response = invoke_with_retry(llm_2, f"""{context_note}Review the following code for bugs, logic errors, unhandled exceptions, 
        off-by-one errors, null/undefined checks, and incorrect conditions. 
        For each bug found, explain what it is, why it's a problem, and suggest 
        a specific fix. Format as numbered list. Code: {state["raw_code"]}""")  
    log_time("bug_reviewer_r1", start)
    return {"bug_review_r1" : response.content}

def security_reviewer_r1(state: AgentState):
    start = time.time()
    time.sleep(2) 
    context = state.get("code_context", "")
    context_note = f"Context about this code: {context}\n" if context else ""
    response = invoke_with_retry(llm_2, f"""{context_note}Review the following code for security vulnerabilities including SQL injection, 
        hardcoded secrets or API keys, unvalidated user inputs, insecure dependencies, 
        exposed sensitive data, and authentication issues. For each vulnerability found, 
        rate its severity (High/Medium/Low), explain the risk, and suggest a fix. 
        Format as numbered list. Code: {state["raw_code"]}""")
    log_time("security_reviewer_r1", start)
    return {"security_review_r1" : response.content}

def performance_reviewer_r1(state: AgentState):
    start = time.time()
    time.sleep(4) 
    context = state.get("code_context", "")
    context_note = f"Context about this code: {context}\n" if context else ""
    response = invoke_with_retry(llm_2, f"""{context_note}Review the following code for performance issues including unnecessary loops, 
        inefficient data structures, redundant API or database calls, memory leaks, 
        blocking operations, and algorithmic complexity issues. For each issue found, 
        explain the impact and suggest an optimized approach. 
        Format as numbered list. Code: {state["raw_code"]}""")
    log_time("performance_reviewer_r1", start)
    return {"performance_review_r1" : response.content}


def bug_reviewer_r2(state: AgentState):
    start = time.time()
    time.sleep(1) 
    context = state.get("code_context", "")
    context_note = f"Context about this code: {context}\n" if context else ""

    bug_r1_short = truncate_code(state["bug_review_r1"], max_chars=500)
    security_r1_short = truncate_code(state["security_review_r1"], max_chars=500)
    performance_r1_short = truncate_code(state["performance_review_r1"], max_chars=500)

    response = invoke_with_retry(llm_2, f"""{context_note}You previously reviewed this code for bugs and found:
        {bug_r1_short}

        Now read what two other specialists found:
        
        Security Reviewer found:
        {security_r1_short}
        
        Performance Reviewer found:
        {performance_r1_short}

        Based on their findings, revise your bug analysis:
        - If their findings reveal a bug you missed, add it
        - If your original finding was actually a false positive given their context, remove it
        - If you disagree with something they flagged as a bug, explain why

        Return your REVISED and FINAL bug analysis as a numbered list.

        Code: {state["raw_code"]}""")
    log_time("bug_reviewer_r2", start)
    return {"bug_review_r2": response.content}

def security_reviewer_r2(state: AgentState):
    start = time.time()
    time.sleep(3) 
    context = state.get("code_context", "")
    context_note = f"Context about this code: {context}\n" if context else ""

    bug_r1_short = truncate_code(state["bug_review_r1"], max_chars=500)
    security_r1_short = truncate_code(state["security_review_r1"], max_chars=500)
    performance_r1_short = truncate_code(state["performance_review_r1"], max_chars=500) 

    response = invoke_with_retry(llm_2, f"""{context_note}You previously reviewed this code for bugs and found:
        {security_r1_short}

        Now read what two other specialists found:
        
        Bug Reviewer found:
        {bug_r1_short}
        
        Performance Reviewer found:
        {performance_r1_short}

        What to check for security analysis: 
        Review the following code for security vulnerabilities including SQL injection, 
        hardcoded secrets or API keys, unvalidated user inputs, insecure dependencies, 
        exposed sensitive data, and authentication issues. For each vulnerability found, 
        rate its severity (High/Medium/Low), explain the risk, and suggest a fix. 

        Based on their findings, revise your security analysis:
        - If their findings reveal a security concern you missed, add it
        - If your original finding was actually a false positive given their context, remove it
        - If you disagree with something they flagged, explain why

        Return your REVISED and FINAL security analysis as a numbered list.

        Code: {state["raw_code"]}""")
    log_time("security_reviewer_r2", start)
    return {"security_review_r2": response.content}

def performance_reviewer_r2(state: AgentState):
    start = time.time()
    time.sleep(5) 
    context = state.get("code_context", "")
    context_note = f"Context about this code: {context}\n" if context else ""

    bug_r1_short = truncate_code(state["bug_review_r1"], max_chars=500)
    security_r1_short = truncate_code(state["security_review_r1"], max_chars=500)
    performance_r1_short = truncate_code(state["performance_review_r1"], max_chars=500)

    response = invoke_with_retry(llm_2, f"""{context_note}You previously reviewed this code for bugs and found:
        {performance_r1_short}

        Now read what two other specialists found:
        
        Bug Reviewer found:
        {bug_r1_short}
        
        Security Reviewer found:
        {security_r1_short}

        What to check for performance analysis: 
        Review the following code for performance issues including unnecessary loops, 
        inefficient data structures, redundant API or database calls, memory leaks, 
        blocking operations, and algorithmic complexity issues. For each issue found, 
        explain the impact and suggest an optimized approach.  

        Based on their findings, revise your performance analysis:
        - If their findings reveal a performance concern you missed, add it
        - If your original finding was actually a false positive given their context, remove it
        - If you disagree with something they flagged, explain why

        Return your REVISED and FINAL performance analysis as a numbered list.

        Code: {state["raw_code"]}""")
    log_time("performance_reviewer_r2", start)
    return {"performance_review_r2": response.content}

def supervisor(state: AgentState):
    start = time.time()
    context = state.get("code_context", "")

    bug_r1_short = truncate_code(state["bug_review_r1"], max_chars=500)
    security_r1_short = truncate_code(state["security_review_r1"], max_chars=500)
    performance_r1_short = truncate_code(state["performance_review_r1"], max_chars=500)

    response = invoke_with_retry(llm, f"""You are the supervisor reviewing all findings from three specialist agents across two rounds of analysis.

    Round 1 findings (independent):
    Bug Reviewer (R1): {bug_r1_short}
    Security Reviewer (R1): {security_r1_short}
    Performance Reviewer (R1): {performance_r1_short}

    Round 2 findings (after specialists debated and revised based on each other):
    Bug Reviewer (R2): {state["bug_review_r2"]}
    Security Reviewer (R2): {state["security_review_r2"]}
    Performance Reviewer (R2): {state["performance_review_r2"]}

    Your job:
    1. Compare R1 vs R2 for each specialist — note what changed and why
    2. Identify which findings are CONFIRMED real issues (specialists agree, or revised finding is well-justified)
    3. Discard findings that were retracted or are false positives based on the debate
    4. Rank confirmed issues by severity: CRITICAL, HIGH, MEDIUM, LOW
    5. Output ONLY confirmed, actionable issues — nothing speculative

    Format your verdict as:
    CRITICAL ISSUES: (must fix)
    HIGH ISSUES: (should fix)
    MEDIUM/LOW ISSUES: (optional, list only, do not elaborate)

    Code: {state["raw_code"]}""")
    log_time("supervisor", start)
    return {"supervisor_verdict": response.content}


def synthesizer(state: AgentState):
    start = time.time()
    response = invoke_with_retry(llm, f"""Take this supervisor's verdict and expand it into a polished, professional code review report.
    For each issue listed, add a brief explanation of why it matters and a suggested fix.
    Structure the report with these sections: Executive Summary, Critical Issues, High Priority Issues, 
    Other Observations, Final Recommendation.
    Keep it clear and readable for someone who didn't see the raw debate process.

    Supervisor Verdict: {state["supervisor_verdict"]}""")
    log_time("sythesizer", start)
    return {"final_report" : response.content}

def code_fixer(state: AgentState):
    start = time.time()
    response = invoke_with_retry(llm, f"""You are fixing ONLY confirmed HIGH severity bugs in the code below.
        STRICT RULES:
        - Do NOT rewrite working code
        - Do NOT fix MEDIUM or LOW severity issues
        - Do NOT add code that wasn't there before
        - Do NOT remove code unless it's a confirmed bug
        - If no HIGH severity issues exist, return the EXACT original code unchanged
        - Only make the minimum changes necessary to fix confirmed HIGH severity bugs

        Original Code:
        {state["raw_code"]}
        
        Review findings:
        {state["supervisor_verdict"]}""")
    log_time("code_fixer", start)
    return {"fixed_code": response.content}

def verify_fix(state: AgentState):
    start = time.time()
    current_count = state.get("iteration_count", 0)
    truncated = truncate_code(state["fixed_code"], max_chars=1500)
    response = invoke_with_retry(llm, f"""Review this code and determine if any CRITICAL bugs remain.
        STRICT RULES:
        - Only flag confirmed bugs that will cause runtime failures
        - Do NOT flag style issues, missing docstrings, or theoretical problems
        - Do NOT flag variables as undefined if they could be defined in parent scope
        - Do NOT flag working production patterns as issues
        - If code looks functional, return NO_ISSUES
        - Only return ISSUES_FOUND if there is a guaranteed runtime error

        At the very end of your response write exactly one of:
        ISSUES_FOUND
        NO_ISSUES

        Fixed Code: {truncated}""")
    log_time("verify fix", start)
    return {"verify_output": response.content, "iteration_count": current_count + 1}

def test_generator(state: AgentState):
    start = time.time()
    print(" test generator running.......")
    response = invoke_with_retry(llm, f"""Generate comprehensive unit tests for the following code. 
        Cover normal cases, edge cases, and error cases. 
        Use pytest format.

        Code: {state["fixed_code"]}""")
    log_time("test_generator", start)
    return {"test_cases": response.content}

