---
title: AI Code Review Agent
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 5.9.1
app_file: app.py
pinned: false
python_version: 3.11
---

# 🔍 AI Code Review Agent

A multi-agent code review system built with LangGraph, where specialist AI agents debate findings, a supervisor reconciles their conclusions, and the code gets automatically fixed and tested — all through a 12-node orchestrated graph.

**Live Demo:** https://harshdubs-ai-code-review-agent.hf.space

---

## What it does

Paste existing code (or a GitHub file URL), or describe what you want built from scratch. The agent:

1. Fetches or generates the code
2. Runs three specialist reviewers (bugs, security, performance) in parallel
3. Has each reviewer **debate** — reading the other two's findings and revising their own conclusions
4. Sends all six rounds of findings to a **supervisor agent** that reconciles disagreements and outputs a prioritized verdict
5. Synthesizes that into a polished report
6. Fixes confirmed high-severity issues in the code
7. Verifies the fix, looping back to re-fix if critical issues remain (up to 2 iterations)
8. Generates unit tests for the final code

## Why multi-agent debate

A single LLM pass tends to either miss issues or hallucinate false positives. Having three specialists independently review, then **read and respond to each other's findings**, surfaces disagreements a single pass would miss — similar to how a second engineer in a code review catches what the first one didn't. The supervisor then filters out anything that was retracted or unconvincing during the debate, so only confirmed issues reach the code fixer.

## Architecture

START

↓

route_entry (conditional: code input vs. description)

↓                              ↓

fetch_code                  code_writer

↓                              ↓

└──────────┬─────────────┘

↓

bug_reviewer_r1 + security_reviewer_r1 + performance_reviewer_r1   (parallel, round 1)

↓

bug_reviewer_r2 + security_reviewer_r2 + performance_reviewer_r2   (parallel, round 2 — debate)

↓

supervisor (reconciles all 6 findings)

↓

synthesizer (polished report)

↓

code_fixer

↓

verify_fix ──┐

↓      │ (loop if issues remain, max 2x)

test_generator

↓

END

## Tech Stack

- **LangGraph** — graph orchestration, parallel nodes, conditional routing, cyclic loops
- **Groq** (`llama-3.1-8b-instant`) — fast inference for the 6 parallel reviewer calls
- **Cerebras** (`gpt-oss-120b`) — supervisor, synthesis, code fixing, and test generation
- **Gradio** — UI with live code editors, tabbed output, and an agent debate log
- **GitHub raw content fetch** — pull code directly from a GitHub file URL

## Features

- Two input modes: paste code/URL, or describe what to build
- Optional context field so reviewers don't flag intentional patterns (e.g. PLC variables defined in a parent scope)
- Visible **Agent Debate Log** — see exactly how each reviewer's opinion changed after reading the others
- Iterative fix-and-verify loop with a hard iteration cap
- Auto-generated pytest test cases for the fixed code
- Rate-limit-aware retry logic across two LLM providers

## Running locally

```bash
git clone https://github.com/harshdubs/ai-code-review-agent
cd ai-code-review-agent
pip install -r requirements.txt
```

Create a `.env` file:
GROQ_API_KEY=your_key

CEREBRAS_API_KEY=your_key

```bash
python app.py
```

## Project Status

Part of a self-directed AI Engineer learning roadmap. Built iteratively — started as a single-pass parallel reviewer, evolved into a debate-pattern multi-agent system with a supervisor and conditional loops.