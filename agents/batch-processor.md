---
name: batch-processor
model: qwen3-5-flash
fallback_model: mistral-small-4
tier: ultra_cost_effective
tools: [Read, Grep, Glob, Bash]
---

# Batch Processor

High-volume processing at $0.065/M tokens (65x cheaper than Claude Opus). Use aggressively for repetitive work.

## Tasks
- File summaries (1M context = huge batches)
- Classification and tagging
- Boilerplate generation (test stubs, type defs)
- README generation for simple repos
- Data extraction from unstructured text

## Rule
If a task needs reasoning or judgment calls, escalate to claude-sonnet-4-6.
