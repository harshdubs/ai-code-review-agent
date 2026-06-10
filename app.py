import gradio as gr
from graph import app

def process(code_input):
    result = app.invoke({
    "code_input": code_input,
    "iteration_count": 0
    })

    return result["fixed_code"], result["final_report"], result["test_cases"]

with gr.Blocks(title="Code Review Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🔍 AI Code Review Agent
    Paste your code or a GitHub file URL. The agent reviews for bugs, security issues, 
    and performance problems — then fixes and tests it automatically.
    """)
    with gr.Row():    
        code_input = gr.Code(language="python", label="Enter Code / Github URL", max_lines=20)

    with gr.Tabs():
        with gr.TabItem("🛠 Fixed Code"):
            fixed_code = gr.Code(language="python", label="Fixed Code", max_lines=20)
        
        with gr.TabItem("📋 Review Report"):
            final_report = gr.Markdown()

        with gr.TabItem("🧪 Test Cases"):
            test_cases = gr.Code(language="python", label="Used Test Cases", lines=10, scale=4)

    status = gr.Markdown("Ready")

    with gr.Row():
        start_button = gr.Button("🚀 Review & Fix", variant="primary", scale=1)
        clear_button = gr.Button("Clear", variant="secondary", scale=1)

    clear_button.click(fn=lambda: ("", "", "", ""), outputs=[code_input, fixed_code, final_report, test_cases])


    start_button.click(
        fn=lambda: "⏳ Analyzing code...",
        outputs=[status]
    ).then(
        fn=process,
        inputs=[code_input],
        outputs=[fixed_code, final_report, test_cases]
    ).then(
        fn=lambda: "✅ Done",
        outputs=[status]
    )


if __name__=="__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
