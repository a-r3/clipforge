# AI Integration

ClipForge works fully without AI by default (`ai_mode = "off"`). An optional
AI layer can improve scene planning quality, query generation, and social pack
output when enabled.

---

## AI modes

| `ai_mode` | Behaviour |
|-----------|-----------|
| `off` *(default)* | Local heuristics only — no API calls |
| `assist` | AI refines scene queries and improves social pack |
| `full` | AI drives scene planning end-to-end |

Set in your config or `.env`:

```json
{
  "ai_mode": "assist",
  "ai_provider": "openai"
}
```

---

## Providers

| `ai_provider` | Env var | Default model |
|---------------|---------|---------------|
| `openai` | `OPENAI_API_KEY` | `gpt-4o-mini` |
| `anthropic` | `ANTHROPIC_API_KEY` | `claude-3-haiku-20240307` |
| `gemini` | `GEMINI_API_KEY` | `gemini-pro` |

Add the matching key to `.env`:

```ini
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
```

Override the model with `ai_model` in your config:

```json
{
  "ai_mode": "assist",
  "ai_provider": "anthropic",
  "ai_model": "claude-sonnet-4-6"
}
```

---

## What AI improves (v0.3+)

### Scene planning (`assist` and `full`)

In `assist` mode the local heuristic planner runs first, then AI refines the
result. The AI receives:
- Scene text and extracted keywords
- The local visual type classification
- The local candidate queries

The AI can override the visual type and improve the primary search query, plus
provide alternate queries used when the primary returns no stock results.

Each planned scene now includes:

```json
{
  "primary_query": "machine learning abstract",
  "alternate_queries": ["AI data visualization", "tech innovation"],
  "confidence": 0.72,
  "visual_type": "technology"
}
```

### Social pack (`assist` and `full`)

AI improves title, hook, and caption copy when `ai_mode` is not `off`.
The local generator always runs as fallback.

---

## Graceful degradation

If the API key is missing, the library is not installed, or the provider
returns an error, ClipForge falls back silently to local heuristics.
No crash, no interruption — just a debug log entry.

---

## Provider implementations

Provider code lives under `src/clipforge/ai/providers/`. The abstract base
class is `clipforge.ai.base.AIProvider`. To add a new provider:

1. Create `src/clipforge/ai/providers/myprovider_provider.py`
2. Subclass `AIProvider` and implement `generate(prompt, schema)`
3. Register it in `AIFactory.get_provider()` in `src/clipforge/ai/factory.py`
