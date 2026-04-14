# Skills Overview

This directory contains all AI agent skills organized by platform.

## Structure

```
skills/
├── common/     # Platform-agnostic, reusable skills
├── gemini/     # Google Gemini
├── copilot/    # GitHub Copilot
├── claude/     # Anthropic Claude
├── zai/        # ZAI
├── openai/     # OpenAI
├── ollama/     # Ollama (local LLMs)
└── mistral/    # Mistral AI
```

## Skill Authoring Guidelines

1. **Prefer `common/`**: If a skill is not model-specific, put it in `common/` so all platforms can reuse it
2. **One skill per directory**: Each skill is a self-contained directory with its own `README.md`
3. **Document inputs/outputs**: Every skill must declare what it accepts and returns
4. **No hard-coded credentials**: Use environment variables from `config/` templates
5. **Dependency declaration**: List any required packages/tools in your skill's README

## Skill Template

```
skills/common/<skill-name>/
├── README.md         # Purpose, inputs, outputs, usage examples
├── skill.json        # Machine-readable skill metadata (optional)
└── <implementation>  # .py, .ts, .js, etc.
```

### skill.json Schema (optional)

```json
{
  "name": "skill-name",
  "description": "What this skill does",
  "platforms": ["common"],
  "inputs": [
    { "name": "param1", "type": "string", "description": "..." }
  ],
  "outputs": [
    { "name": "result", "type": "string", "description": "..." }
  ],
  "dependencies": []
}
```
