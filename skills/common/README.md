# Common / Shared AI Skills

Skills placed in this directory are **platform-agnostic** and can be used by any AI agent regardless of the underlying model or provider.

## Conventions

- Each skill is a self-contained directory with its own `README.md`
- Skills must document their inputs, outputs, and any dependencies
- Skills should not hard-code provider-specific API calls — use the abstraction layer in `tools/`

## Available Skills

| Skill | Description |
|-------|-------------|
| *(add skills here)* | |

## Adding a New Common Skill

1. Create a new directory under `skills/common/<skill-name>/`
2. Add a `README.md` describing the skill's purpose, inputs, and outputs
3. Add the skill implementation file(s)
4. If the skill works on only some platforms, move it to the appropriate platform directory instead
