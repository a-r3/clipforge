## Workflows

This document describes recommended workflows for using `clipforge`.

### Single Video Creation

1. Write your script in a plain text file.
2. Run `clipforge scenes --script-file your_script.txt` to preview how it will be segmented.
3. Run `clipforge make --script-file your_script.txt --output output.mp4` to build the video.
4. Optionally generate a social pack with `clipforge social-pack`.

### Batch Processing

1. Create a batch configuration JSON using `clipforge init-batch --output batch.json`.
2. Edit the file to add multiple job entries.
3. Run `clipforge batch --batch-file batch.json` to process all jobs.
