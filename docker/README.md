# Docker Usage

Run Claude Code with pre-configured MCP servers in an isolated container.

## Quick Start

```bash
# Build the image
docker build -t ai-agent-skills -f docker/Dockerfile .

# Run with your credentials
docker run -it \
  --env-file ~/VSCodespace/.env \
  -v $(pwd):/workspace \
  ai-agent-skills

# Or with Docker Compose (MCP servers as separate services)
cp docker/.env.example .env   # fill in your values
docker-compose -f docker/docker-compose.yml up
```

## What's included

| Component | Details |
|-----------|---------|
| Base image | `node:lts-slim` |
| Claude Code CLI | Pre-installed globally |
| MCP servers | github, filesystem, context7 pre-cached |
| Profile | `docker` (minimal — no azure, no jira) |
| Workspace | Mounted at `/workspace` |

## Secrets

Never bake secrets into the image. Pass at runtime:
- `--env-file ~/VSCodespace/.env`  (local)
- CI secrets → environment variables  (GitHub Actions, etc.)

## Extending

To add more MCP servers for a specific project, add a `.mcp.json` to your project root:
```json
{
  "mcpServers": {
    "perplexity": {
      "command": "npx",
      "args": ["-y", "perplexity-mcp"],
      "env": { "PERPLEXITY_API_KEY": "..." }
    }
  }
}
```

## CI/CD (GitHub Actions example)

```yaml
- name: Run Claude Code agent
  uses: docker://ghcr.io/brackenw3/ai-agent-skills:latest
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    GITHUB_MCP_PAT: ${{ secrets.GITHUB_MCP_PAT }}
```
