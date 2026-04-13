# OpenAI Skills

Skills specific to **OpenAI** models and APIs (GPT-4, GPT-4o, DALL-E, Whisper, Embeddings, etc.).

## Configuration

Requires the following environment variables (see `config/vscode/.env.template`):

```
OPENAI_API_KEY=<your-openai-api-key>
OPENAI_ORG_ID=<your-openai-organization-id>   # optional
```

## Available Skills

| Skill | Model | Description |
|-------|-------|-------------|
| *(add skills here)* | | |

## Notes

- OpenAI skills use the [OpenAI Python/JS SDK](https://platform.openai.com/docs/libraries)
- For image generation use DALL-E 3; for transcription use Whisper
- Platform-agnostic skills belong in `skills/common/`
