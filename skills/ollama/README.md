# Ollama Skills

Skills for **Ollama** — run large language models locally without sending data to external APIs.

## Configuration

Requires the following environment variables (see `config/vscode/.env.template`):

```
OLLAMA_HOST=http://localhost:11434   # default local Ollama host
OLLAMA_MODEL=llama3                  # default model to use
```

## Available Skills

| Skill | Model | Description |
|-------|-------|-------------|
| *(add skills here)* | | |

## Notes

- Ollama runs entirely on your local machine — no API keys required for local usage
- Install Ollama from [https://ollama.ai](https://ollama.ai)
- Pull models with `ollama pull <model-name>` before use
- Platform-agnostic skills belong in `skills/common/`
