---
name: debugger-llama-stack
description: >
  Use when analyzing "llama_stack" component failures from RHOAI test results.
  Covers LlamaStack operator, LLM orchestration, and GPU resource requirements.
allowed-tools: Bash(*/debugger-llama-stack/scripts/*.sh:*),Bash(*/debugger-llama-stack/scripts/*.py:*),Bash(*/tools/rp-client/*.py:*),Bash(*/tools/must-gather/*.py:*)
---

# LlamaStack Debugger

## RP Component
This skill handles the `llama_stack` component from ReportPortal launches.

## Key Concepts

- LlamaStack operator for LLM orchestration
- Requires significant GPU resources
- Long startup times for large models (Llama 70B+)

## Known Failure Patterns

### Product Bugs
- `LlamaStack.*not.*found` → Operator CRD not installed
- `failed to reconcile.*llamastack` → Operator controller error

### Infrastructure Issues
- `Insufficient.*nvidia|GPU.*unavailable` → Not enough GPU nodes
- `OOMKilled` → Model too large for available memory
- `timeout` with large models → Startup takes 15-30 min for 70B models

### Test Automation Issues
- Short timeout for large model startup → Needs 15-30 min

## Diagnosis Steps

1. Read test failure logs
2. Check if LlamaStack CRD/operator is installed
3. If cluster access available, run `scripts/inspect_llama_stack.sh`
4. Check GPU availability and memory on nodes
5. Classify and output structured JSON
