## Extensions

This document describes optional extensions and future enhancements that can be added to `autovideo`.

### AI Integration

Support for different AI providers can be added by implementing subclasses of `AIProvider` in `src/autovideo/ai/providers`. Providers should generate scene plans and social packs as structured data.

### GUI Studio

The planned `studio` subcommand will provide a graphical user interface for fine‑grained editing. It will integrate a timeline editor, drag‑and‑drop media and real‑time previews.

### Publishing API

Future versions may include a `publish` subcommand to upload the generated video and social metadata directly to social platforms. Authentication and API interactions would be encapsulated in a separate module.
