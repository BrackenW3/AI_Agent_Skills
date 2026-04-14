# syntax=docker/dockerfile:1
# AI Agent Skills — Claude Code development container
# Minimal image: Node LTS + Python 3 + Claude Code CLI + pre-cached MCP servers
# Usage: docker build -t ai-agent-skills . && docker run --env-file ~/VSCodespace/.env -v $(pwd):/workspace ai-agent-skills

ARG NODE_VERSION=lts
FROM node:${NODE_VERSION}-slim AS base

# Install Python 3, git, curl (needed by bootstrap and MCP servers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code --prefer-offline 2>/dev/null || \
    npm install -g @anthropic-ai/claude-code

# Pre-cache MCP server packages to avoid npx download on first use
# These are the docker-profile servers (minimal set)
RUN npm install -g \
    @modelcontextprotocol/server-github \
    @modelcontextprotocol/server-filesystem \
    @upstash/context7-mcp \
    && npm cache clean --force

# Create workspace directory
WORKDIR /workspace

# Copy registry (config files only — no secrets)
COPY --chown=node:node . /opt/ai-agent-skills

# Copy and run bootstrap (writes MCP configs using env vars at runtime)
COPY scripts/bootstrap.sh /usr/local/bin/bootstrap-agent
RUN chmod +x /usr/local/bin/bootstrap-agent

# Switch to non-root node user
USER node

# Write MCP configs at container start using injected env vars
ENTRYPOINT ["/bin/sh", "-c", "REGISTRY_ROOT=/opt/ai-agent-skills bash /opt/ai-agent-skills/scripts/sync.sh --profile docker && exec \"$@\"", "--"]
CMD ["claude"]
