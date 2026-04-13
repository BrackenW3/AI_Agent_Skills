# Config Directory

This directory contains environment variable **templates** for all third-party services and integrations used by AI agent skills and tools in this repository.

## ⚠️ Security Warning

- `.env.template` files contain **placeholder variable names only** — no real credentials
- **Never** put real credentials into `.env.template` files
- Copy template files to `.env` and fill in your values locally
- `.env` files are gitignored and will never be committed

## Service Templates

| Directory | Service | Template |
|-----------|---------|----------|
| `vscode/` | VS Code + all AI extensions | [`.env.template`](vscode/.env.template) |
| `n8n/` | n8n workflow automation | [`.env.template`](n8n/.env.template) |
| `atlassian/` | Jira, Confluence, Bitbucket | [`.env.template`](atlassian/.env.template) |
| `cloudflare/` | Cloudflare DNS, Workers, R2, Pages | [`.env.template`](cloudflare/.env.template) |

## Setup Instructions

For each service you use:

```bash
# 1. Copy the template to a local .env file
cp config/<service>/.env.template config/<service>/.env

# 2. Open the .env file and fill in your credentials
#    (Use a text editor or your secrets manager)

# 3. Verify .env is gitignored
git status config/<service>/.env
# Should show: nothing to commit (file is ignored)
```

For full setup instructions, see [docs/setup.md](../docs/setup.md).
