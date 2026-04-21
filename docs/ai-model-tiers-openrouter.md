# AI Model Tier Architecture — OpenRouter Multi-Provider Strategy
**Date**: 2026-04-20 | **Status**: Active Design

---

## Overview

Moving from a 6-provider flat config to a **branched tier system** with specialized agents. Key principles:
- Cost optimization via smart routing (free → cheap → mid → premium → frontier)
- Specialized agents for domain expertise (not just model swaps)
- Shared skills/tools/MCPs across agents via AI_Agent_Skills
- BYOK across all providers via OpenRouter (one API key, 200+ models)
- Local LLM (Ollama) as zero-cost fallback for private/high-volume tasks

---

## Provider Access Summary

| Provider | Key Available | Access Method | Cost |
|----------|--------------|---------------|------|
| OpenRouter | ✅ OPENROUTER_API_KEY | Unified gateway | Per model |
| Anthropic | ✅ ANTHROPIC_API_KEY | Direct + OpenRouter | Per token |
| OpenAI | ✅ OPENAI_API_KEY | Direct + OpenRouter | Per token |
| Google Gemini | ✅ GEMINI_API_KEY | Direct + OpenRouter | Per token |
| Z.AI / GLM | ✅ ZAI_API_KEY | Direct + OpenRouter | Per token |
| xAI / Grok | ✅ XAI_API_KEY | Direct + OpenRouter | Per token |
| Mistral | ✅ MISTRAL_API_KEY | Direct + OpenRouter | Per token |
| GitHub Models | ✅ GH_TOKEN | GitHub endpoint | Free (60 RPM) |
| HuggingFace | ✅ HF_TOKEN | Inference API | Free tier |
| Ollama | ✅ OLLAMA_API_BASE | Local | Zero cost |
| Perplexity | ✅ PERPLEXITY_API_KEY | Direct | Per query |

**Strategy**: Use OpenRouter as the unified gateway. Direct provider access for high-volume or subscription-included models.

---

## Model Tiers

### Tier 0 — Local / Zero Cost
| Model | Context | Notes |
|-------|---------|-------|
| Ollama local | Varies | Zero cost, private |
| GitHub Models | 128K | 60 RPM free |

### Tier 1 — Ultra Cheap ($0.065–0.40/M input)
| Model | Input/M | Strengths |
|-------|---------|----------|
| Qwen3.5-Flash | $0.065 | Fast, multimodal, 1M ctx |
| MiMo-V2-Flash | $0.09 | MoE open-source |
| Mistral Small 4 | $0.15 | Image support |
| GLM 4.7 (Z.AI) | $0.38 | Agent+terminal |

### Tier 2 — Cost-Effective ($0.22–0.78/M input)
| Model | Input/M | Strengths |
|-------|---------|----------|
| Devstral 2 | $0.40 | **Best cheap coding agent** |
| Kimi K2.6 | $0.60 | Strong multimodal |
| Mercury 2 | $0.25 | Fast reasoning |

### Tier 3 — Balanced ($0.70–3.00/M input) — 80% of workload
| Model | Input/M | Strengths |
|-------|---------|----------|
| Claude Sonnet 4.6 | $3.00 | Primary coding, 1M ctx |
| Grok 4.20 | $2.00 | 2M ctx + web search |
| Gemini 3.1 Pro | $2.00 | Audio/video/image |
| GLM 5.1 | $0.70 | Agentic, 7x cheaper than Sonnet |

### Tier 4 — Premium ($5.00+/M input)
| Model | Input/M | Strengths |
|-------|---------|----------|
| Claude Opus 4.7 | $5.00 | **Best reasoning, orchestration** |
| Claude Opus 4.6 Batch | $2.50 | 50% off, 24hr turnaround |

### Tier 5 — Frontier (use sparingly)
| Model | Input/M | When |
|-------|---------|------|
| GPT-5.4 Pro | $30.00 | Absolute highest stakes only |

---

## Agent Fleet

| Agent | Primary | Fallback | Role |
|-------|---------|---------|------|
| orchestrator-prime | Claude Opus 4.7 | Claude Sonnet 4.6 | Master orchestrator |
| task-planner | GLM 5.1 | Claude Sonnet 4.6 | Planning, specs |
| research-analyst | Grok 4.20 | Gemini 3.1 Pro | Web research |
| code-engineer | Claude Sonnet 4.6 | GLM 5.1 | General coding (60% of work) |
| code-architect | Claude Opus 4.7 | Claude Sonnet 4.6 | Architecture decisions |
| code-reviewer | Claude Sonnet 4.6 | Devstral 2 | PR review (one per PR) |
| code-cheap | Devstral 2 | GLM 4.7 | Tests, boilerplate |
| security-auditor | Claude Opus 4.7 | GPT-5.4 | Security review |
| data-analyst | Gemini 3.1 Pro | Claude Sonnet 4.6 | DuckDB/SQL/pandas |
| batch-processor | Qwen3.5-Flash | Mistral Small 4 | Bulk/summaries |
| local-private | Ollama | Claude Haiku | Sensitive data |

---

## Anti-Patterns

| Pattern | Fix |
|---------|-----|
| Multiple AIs reviewing same PR | One reviewer per PR |
| Frontier model for simple tasks | Route to T1/T2 |
| No caching | L1+L3 cache required |
| AI losing context mid-task | Checkpoint every 30 min |
| Jules 30 PRs/day | Weekly batch PR workflow |

---

## Monthly Budget Target: $100

| Tier | Budget | % |
|------|--------|---|
| Free/Local | $0 | - |
| T1 batch | $5 | 5% |
| T2 cost-effective | $10 | 10% |
| T3 balanced | $40 | 40% |
| T4 premium | $30 | 30% |
| T5 frontier | $15 | 15% |
