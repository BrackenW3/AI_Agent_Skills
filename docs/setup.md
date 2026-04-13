# Setup & Onboarding Guide

This guide walks you through setting up the AI Agent Skills repository on a new machine.

## Prerequisites

- Git
- Node.js ≥ 18 (for JavaScript/TypeScript skills)
- Python ≥ 3.10 (for Python skills)
- [Ollama](https://ollama.ai) (optional, for local LLM skills)

## 1. Clone the Repository

```bash
git clone https://github.com/BrackenW3/AI_Agent_Skills.git
cd AI_Agent_Skills
```

## 2. Configure Environment Variables

Copy and fill in the template files for each service you use:

```bash
# VS Code / AI Extensions
cp config/vscode/.env.template config/vscode/.env

# n8n workflow automation
cp config/n8n/.env.template config/n8n/.env

# Atlassian (Jira / Confluence)
cp config/atlassian/.env.template config/atlassian/.env

# Cloudflare
cp config/cloudflare/.env.template config/cloudflare/.env
```

Open each `.env` file and fill in your credentials. See the sections below for where to obtain each credential.

## 3. Obtain API Keys

### GitHub / Copilot

1. Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Create a new token with scopes: `repo`, `read:org`, `copilot`
3. Set `GITHUB_TOKEN` in `config/vscode/.env`

### OpenAI

1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Create a new secret key
3. Set `OPENAI_API_KEY` in `config/vscode/.env`

### Anthropic / Claude

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an API key
3. Set `ANTHROPIC_API_KEY` in `config/vscode/.env`

### Google / Gemini

1. Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Set `GEMINI_API_KEY` in `config/vscode/.env`

### Mistral AI

1. Go to [console.mistral.ai](https://console.mistral.ai)
2. Create an API key
3. Set `MISTRAL_API_KEY` in `config/vscode/.env`

### Atlassian (Jira / Confluence)

1. Go to [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Create a new API token
3. Set `ATLASSIAN_EMAIL`, `ATLASSIAN_API_TOKEN`, and `ATLASSIAN_BASE_URL` in `config/atlassian/.env`

### Cloudflare

1. Go to [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens)
2. Create a scoped API token (recommended scopes: Zone:Read, DNS:Edit, Workers Scripts:Edit)
3. Set `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` in `config/cloudflare/.env`
   - Your Account ID is shown in the sidebar of the Cloudflare dashboard

### n8n

1. Generate a strong random string for `N8N_ENCRYPTION_KEY` (e.g. `openssl rand -hex 32`)
2. Set your database credentials if not using the default SQLite
3. Set `WEBHOOK_URL` to your public-facing n8n URL
4. Fill in any third-party credentials in `config/n8n/.env`

## 4. Set Up Ollama (Local LLMs — Optional)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3
ollama pull mistral
ollama pull codellama

# Verify it's running
curl http://localhost:11434/api/tags
```

## 5. MCP Server Setup

To use MCP servers with Claude Desktop or VS Code extensions:

1. Review available servers in [`tools/mcp/README.md`](../tools/mcp/README.md)
2. Add MCP server entries to your local AI client config (see MCP README for paths)
3. Reference environment variables using `${VAR_NAME}` syntax in MCP config files

## 6. Syncing Across Machines

This repository is designed to be cloned on each machine you use. To sync:

1. Commit new skills and tool configurations to this repo
2. On each new machine, run `git pull` and then copy each template:
   ```bash
   cp config/vscode/.env.template config/vscode/.env
   cp config/n8n/.env.template config/n8n/.env
   cp config/atlassian/.env.template config/atlassian/.env
   cp config/cloudflare/.env.template config/cloudflare/.env
   ```
   Then fill in your credentials in each `.env` file.
3. Use a **secrets manager** (e.g. 1Password, Bitwarden, AWS Secrets Manager) to store and retrieve actual credential values — never store them in this repo

## Security Checklist

- [ ] All `.env` files are gitignored (run `git status` to verify)
- [ ] No API keys appear in `.env.template` files
- [ ] `git log --all --full-history -- "**/.env"` returns nothing sensitive
- [ ] MCP config files use `${VAR_NAME}` placeholders, not real keys
