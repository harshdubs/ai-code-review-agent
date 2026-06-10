from langgraph.graph import END,START,StateGraph
from nodes import fetch_code, bug_reviewer, security_reviewer, performance_reviewer, report_generator, code_fixer, verify_fix, test_generator
from state import AgentState

def should_continue(state: AgentState):
    if "ISSUES_FOUND" in state["verify_output"] and state["iteration_count"] <2:
        return "code_fixer"
    return "test_generator"

graph = StateGraph(AgentState)

graph.add_node("fetch_code", fetch_code)
graph.add_node("bug_reviewer", bug_reviewer)
graph.add_node("security_reviewer", security_reviewer)
graph.add_node("performance_reviewer", performance_reviewer)
graph.add_node("report_generator", report_generator)
graph.add_node("code_fixer", code_fixer)
graph.add_node("verify_fix", verify_fix)
graph.add_node("test_generator", test_generator)

graph.add_edge(START, "fetch_code")

graph.add_edge("fetch_code", "bug_reviewer")
graph.add_edge("fetch_code", "security_reviewer")
graph.add_edge("fetch_code", "performance_reviewer")
graph.add_edge("performance_reviewer", "report_generator")
graph.add_edge("bug_reviewer", "report_generator")
graph.add_edge("security_reviewer", "report_generator")

graph.add_edge("report_generator", "code_fixer")
graph.add_edge("code_fixer","verify_fix")
graph.add_conditional_edges("verify_fix", should_continue)

graph.add_edge("test_generator", END)

app = graph.compile()