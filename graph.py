from langgraph.graph import END,START,StateGraph
from nodes import fetch_code, code_writer, bug_reviewer_r1, security_reviewer_r1, performance_reviewer_r1, code_fixer, verify_fix, test_generator,bug_reviewer_r2, security_reviewer_r2, performance_reviewer_r2, supervisor, synthesizer
from state import AgentState

def should_continue(state: AgentState):
    if "ISSUES_FOUND" in state["verify_output"] and state["iteration_count"] <2:
        return "code_fixer"
    return "test_generator"

def route_entry(state: AgentState):
    if state.get("user_description"):
        return "code_writer"
    return "fetch_code"

graph = StateGraph(AgentState)

graph.add_node("code_writer",code_writer)
graph.add_node("fetch_code", fetch_code)
graph.add_node("bug_reviewer_r1", bug_reviewer_r1)
graph.add_node("security_reviewer_r1", security_reviewer_r1)
graph.add_node("performance_reviewer_r1", performance_reviewer_r1)
graph.add_node("bug_reviewer_r2", bug_reviewer_r2)
graph.add_node("security_reviewer_r2", security_reviewer_r2)
graph.add_node("performance_reviewer_r2", performance_reviewer_r2)
graph.add_node("supervisor", supervisor)
graph.add_node("synthesizer", synthesizer)
graph.add_node("code_fixer", code_fixer)
graph.add_node("verify_fix", verify_fix)
graph.add_node("test_generator", test_generator)

graph.add_conditional_edges(START, route_entry)

graph.add_edge("code_writer", "bug_reviewer_r1")
graph.add_edge("code_writer", "security_reviewer_r1")
graph.add_edge("code_writer", "performance_reviewer_r1")

graph.add_edge("fetch_code", "bug_reviewer_r1")
graph.add_edge("fetch_code", "security_reviewer_r1")
graph.add_edge("fetch_code", "performance_reviewer_r1")

graph.add_edge("bug_reviewer_r1", "bug_reviewer_r2")
graph.add_edge("security_reviewer_r1", "security_reviewer_r2")
graph.add_edge("performance_reviewer_r1", "performance_reviewer_r2")

graph.add_edge("performance_reviewer_r2", "supervisor")
graph.add_edge("bug_reviewer_r2", "supervisor")
graph.add_edge("security_reviewer_r2", "supervisor")

graph.add_edge("supervisor", "synthesizer")
graph.add_edge("synthesizer", "code_fixer")
graph.add_edge("code_fixer","verify_fix")
graph.add_conditional_edges("verify_fix", should_continue)

graph.add_edge("test_generator", END)

app = graph.compile()