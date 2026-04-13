# AI Integration

The Auto Scenario Video Builder includes a skeleton for integrating external AI providers to enhance scene planning, query generation and social media caption creation.

Currently the AI functionality is optional and disabled by default. The following providers are planned:

* **OpenAI**: Use GPT models to generate scene breakdowns and search queries.
* **Anthropic**: Alternative large language models for content analysis.
* **Gemini**: Google Gemini API for multimodal content.

Configuration is controlled via environment variables in `.env`:

```
AI_PROVIDER=openai  # or anthropic, gemini, off
AI_MODEL=gpt-4
OPENAI_API_KEY=<your_key>
```

Provider implementations live under `src/clipforge/ai/providers/`.  Refer to `src/clipforge/ai/provider.py` for the abstract interface.