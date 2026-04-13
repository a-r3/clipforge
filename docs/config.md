# Configuration

The `clipforge` command accepts many options to control how videos are produced. For complex projects you can store these options in a JSON configuration file.

Example configuration:

```json
{
  "script_file": "examples/script_example.txt",
  "output": "output/demo.mp4",
  "platform": "reels",
  "style": "clean",
  "audio_mode": "voiceover+music",
  "text_mode": "subtitle",
  "subtitle_mode": "word-by-word",
  "music_file": "assets/music/background.mp3",
  "auto_voice": true
}
```

You can override any of these keys via command line options. See `clipforge --help` for details.