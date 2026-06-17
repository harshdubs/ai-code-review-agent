import gradio as gr
from graph import app

def process(code_input, code_context):
    result = app.invoke({
    "code_input": code_input,
    "code_context": code_context,
    "iteration_count": 0
    })
    debate_log = f"""
    ## Round 1 — Independent Findings

    **Bug Reviewer:**
    {result["bug_review_r1"]}

    **Security Reviewer:**
    {result["security_review_r1"]}

    **Performance Reviewer:**
    {result["performance_review_r1"]}

    ## Round 2 — After Debate

    **Bug Reviewer (revised):**
    {result["bug_review_r2"]}

    **Security Reviewer (revised):**
    {result["security_review_r2"]}

    **Performance Reviewer (revised):**
    {result["performance_review_r2"]}

    ## Supervisor Verdict

    {result["supervisor_verdict"]}
    """
    return result["fixed_code"], result["final_report"], result["test_cases"], debate_log

with gr.Blocks(title="Code Review Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🔍 AI Code Review Agent
    Paste your code or a GitHub file URL. The agent reviews for bugs, security issues, 
    and performance problems — then fixes and tests it automatically.
    """)
    with gr.Row():    
        code_input = gr.Code(language="python", label="Enter Code / Github URL", max_lines=20)

    code_context = gr.Textbox(
        label="Code Context (optional)", 
        placeholder="Describe what this code does, e.g. 'This is a tank control PLC function block, variables are defined in parent program'",
        lines=3
        )

    with gr.Tabs():
        with gr.TabItem("🛠 Fixed Code"):
            fixed_code = gr.Code(language="python", label="Fixed Code", max_lines=20)
        
        with gr.TabItem("📋 Review Report"):
            final_report = gr.Markdown()

        with gr.TabItem("🧪 Test Cases"):
            test_cases = gr.Code(language="python", label="Used Test Cases", lines=10, scale=4)

        with gr.TabItem("💬 Agent Debate Log"):
            debate_log_output = gr.Markdown()

    status = gr.Markdown("Ready")

    

    with gr.Row():
        start_button = gr.Button("🚀 Review & Fix", variant="primary", scale=1)
        clear_button = gr.Button("Clear", variant="secondary", scale=1)

    clear_button.click(fn=lambda: ("", "", "", "", ""), outputs=[code_input, fixed_code, final_report, test_cases, debate_log_output])


    start_button.click(
        fn=lambda: "⏳ Analyzing code...",
        outputs=[status]
    ).then(
        fn=process,
        inputs=[code_input, code_context],
        outputs=[fixed_code, final_report, test_cases, debate_log_output]
    ).then(
        fn=lambda: "✅ Done",
        outputs=[status]
    )


if __name__=="__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
