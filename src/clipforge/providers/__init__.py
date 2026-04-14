"""Provider abstractions for ClipForge.

Providers are pluggable backends for stock media, TTS, and (future) publishing.
Each domain has an abstract base class in its sub-package.

Layout:

    providers/
        stock/      StockProvider  — fetch royalty-free media
        tts/        TTSProvider    — generate voice audio
        publish/    PublishProvider — (future) post to social platforms
"""
