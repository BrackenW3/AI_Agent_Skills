# Google Gemini Skills

Skills specific to the **Google Gemini** family of models (Gemini Pro, Gemini Flash, Gemini Ultra, etc.).

## Configuration

Requires the following environment variable (see `config/vscode/.env.template`):

```
GEMINI_API_KEY=<your-google-ai-api-key>
```

## Available Skills

| Skill | Model | Description |
|-------|-------|-------------|
| *(add skills here)* | | |

## Notes

- Gemini skills use the [Google AI SDK](https://ai.google.dev/)
- For multimodal tasks (images, audio, video) prefer Gemini Pro Vision
- Platform-agnostic skills belong in `skills/common/`
