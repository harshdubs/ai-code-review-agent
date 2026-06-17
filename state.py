from typing import TypedDict

class AgentState(TypedDict):
    code_input: str
    raw_code: str
    final_report: str
    
    bug_review_r1: str
    security_review_r1: str
    performance_review_r1: str
    
    bug_review_r2: str
    security_review_r2: str
    performance_review_r2: str

    fixed_code: str          
    verify_output: str       
    iteration_count: int     
    test_cases: str 
    code_context: str

    supervisor_verdict: str
    debate_log: str