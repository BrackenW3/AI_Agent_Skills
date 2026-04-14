# AI Agent Skills

A centralized repository for shared AI skills, tools, and MCP (Model Context Protocol) configurations across multiple AI platforms — **Gemini, GitHub Copilot, Claude (Anthropic), ZAI, OpenAI, Ollama, Mistral**, and others.

## Goals

- **Standardize** AI skills and tools so they work consistently across platforms
- **Reduce duplication** — write once, use everywhere
- **Sync knowledge** across local machines and AI agents
- **Centralize configuration** with template files for all third-party integrations

## Repository Structure

```
AI_Agent_Skills/
├── skills/
│   ├── common/         # Skills shared across all AI platforms
│   ├── gemini/         # Google Gemini-specific skills
│   ├── copilot/        # GitHub Copilot-specific skills
│   ├── claude/         # Anthropic Claude-specific skills
│   ├── zai/            # ZAI-specific skills
│   ├── openai/         # OpenAI-specific skills
│   ├── ollama/         # Ollama (local LLM) skills
│   └── mistral/        # Mistral AI-specific skills
├── tools/
│   └── mcp/            # Model Context Protocol server configurations
├── config/
│   ├── vscode/         # VS Code environment variable templates
│   ├── n8n/            # n8n workflow automation templates
│   ├── atlassian/      # Atlassian (Jira/Confluence) templates
│   └── cloudflare/     # Cloudflare templates
└── docs/
    └── setup.md        # Onboarding and setup guide
```

## Quick Start

1. Clone this repository
2. Copy the relevant `.env.template` files to `.env` in each `config/` subdirectory
3. Fill in your credentials (see [docs/setup.md](docs/setup.md) for details)
4. **Never commit `.env` files** — they are gitignored by default

## Environment Variables

Template files for all integrations live under `config/`. See each subdirectory for the list of required variables:

| Service      | Template Path                          |
|--------------|----------------------------------------|
| VS Code      | `config/vscode/.env.template`          |
| n8n          | `config/n8n/.env.template`             |
| Atlassian    | `config/atlassian/.env.template`       |
| Cloudflare   | `config/cloudflare/.env.template`      |

## Supported AI Platforms

| Platform        | Skills Dir        | Notes                                 |
|-----------------|-------------------|---------------------------------------|
| Google Gemini   | `skills/gemini/`  | Gemini Pro / Flash API                |
| GitHub Copilot  | `skills/copilot/` | GitHub Copilot agent skills           |
| Anthropic Claude| `skills/claude/`  | Claude 3.x API                        |
| ZAI             | `skills/zai/`     | ZAI platform                          |
| OpenAI          | `skills/openai/`  | GPT-4, DALL-E, Whisper, etc.          |
| Ollama          | `skills/ollama/`  | Local LLM inference                   |
| Mistral AI      | `skills/mistral/` | Mistral API                           |
| Common/Shared   | `skills/common/`  | Platform-agnostic, reusable skills    |

## Contributing

1. Add new skills to `skills/common/` when they are platform-agnostic
2. Place platform-specific skills in the appropriate `skills/<platform>/` directory
3. Document new tools in `tools/mcp/README.md`
4. Never commit secrets or credentials — always use `.env.template` patterns
