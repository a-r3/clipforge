# Frequently Asked Questions

**Q: Why does the tool default to silent mode?**  
A: Without API keys the tool cannot download stock media or voice‑over audio. It therefore defaults to silent mode for safety.

**Q: How do I enable AI features?**  
A: Add an `AI_PROVIDER` and API key in your `.env` file. See `docs/ai.md` for details. The current release includes only the integration skeleton.

**Q: Can I batch process multiple scripts?**  
A: Yes. Use the `init-batch` command to generate a batch configuration and `batch` to process it.
