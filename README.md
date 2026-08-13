# SubBake

The easiest way to embed subtitles into MKV / MP4 / WebM — as a muxed track, not a burn-in.

## Features

- Multi-format subtitles: SMI, SRT, ASS, SSA, VTT, SUP (PGS) with automatic detection
- SMI fansub colors preserved via SMI to ASS conversion (per-speaker styling survives)
- Multi-container output: MKV, MP4, WebM with automatic per-container codec selection
- Drag and drop or click to browse — files and folders, mixed multi-select
- Automatic pairing of same-named video and subtitle files (subfolder-safe)
- Live per-file progress via FFmpeg -progress, overall queue progress
- Sync offset adjustment in 100 ms steps (±30 s)
- Safe cancellation: queued tasks drop out, running tasks stop cleanly
- Encoding auto-detection (chardet, EUC-KR fallback) for legacy Korean subtitles
- English / Korean UI with a runtime language toggle
- Bundled FFmpeg — single executable, nothing else to install

## Usage

1. Launch the application with `python main.py`.
2. Drag video files and subtitle files onto the drop area.
3. Choose the desired output subtitle format (ASS or SRT).
4. Click **Convert** to generate the converted subtitle or **Mux** to embed it into the video.

## License

This project is licensed under the GPL-3.0 license – see the [LICENSE](LICENSE) file for details.
