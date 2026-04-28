# LangFuse Setup Guide
# Your instance: https://langfuse.orangegrass-ad6d20d5.eastus.azurecontainerapps.io

## Step 1 — First Login
1. Go to: https://langfuse.orangegrass-ad6d20d5.eastus.azurecontainerapps.io
2. Login: will@willbracken.com / WillBracken2026!
3. You'll see the dashboard — empty until calls start flowing

## Step 2 — Get Your API Keys
1. Settings → API Keys → Create new key
2. You'll get:
   - Public key:  pk-lf-...
   - Secret key:  sk-lf-...
3. Save both — add to your .env:
   LANGFUSE_PUBLIC_KEY=pk-lf-xxxxx
   LANGFUSE_SECRET_KEY=sk-lf-xxxxx
   LANGFUSE_HOST=https://langfuse.orangegrass-ad6d20d5.eastus.azurecontainerapps.io

## Step 3 — What You See (after calls start flowing)
- Traces: every AI call with full input/output
- Cost per call, per model, per day
- Latency graphs
- Error rates
- Which prompts work, which don't

## Step 4 — Add to Your Code (optional, LiteLLM handles this automatically)
# Python
from langfuse.openai import openai  # drop-in replacement
client = openai.OpenAI(api_key="...")
response = client.chat.completions.create(...)  # auto-logged

# n8n — just use LiteLLM endpoint, logging is automatic

## What LangFuse Tracks Automatically (via LiteLLM)
- Model used
- Input/output tokens
- Cost in USD
- Latency
- Success/failure
- Which app/agent made the call

## Projects to Create in LangFuse
- "n8n workflows"    — tag all n8n calls
- "vector-search"   — embedding calls
- "claude-code"     — Claude Code sessions
- "willbracken.com" — website AI features
