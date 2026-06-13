from typing import TypedDict

class AgentState(TypedDict):
    code_input: str
    raw_code: str
    bug_review: str
    security_review: str
    performance_review: str
    final_report: str

    fixed_code: str          
    verify_output: str       
    iteration_count: int     
    test_cases: str 
    code_context: str