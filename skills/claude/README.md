# Anthropic Claude Skills

Skills specific to **Anthropic Claude** models (Claude 3 Haiku, Sonnet, Opus, etc.).

## Configuration

Requires the following environment variable (see `config/vscode/.env.template`):

```
ANTHROPIC_API_KEY=<your-anthropic-api-key>
```

## Available Skills

| Skill | Model | Description |
|-------|-------|-------------|
| *(add skills here)* | | |

## Notes

- Claude skills use the [Anthropic Python/JS SDK](https://docs.anthropic.com/en/api/getting-started)
- For long-context tasks prefer Claude 3 Opus or Sonnet
- Platform-agnostic skills belong in `skills/common/`
