# SubBake

A lightweight desktop application for converting and muxing subtitle files with video. It provides a simple drag‑and‑drop GUI built with Python.

## Features

- Convert between **ASS** and **SRT** subtitle formats.
- Automatically download and use **FFmpeg** for muxing subtitles into video files.
- Detect and handle various text encodings.
- Straightforward GUI for selecting input files, output format, and destination.

## Project Structure

```
download_ffmpeg.py      # Script that downloads FFmpeg binaries if not present
main.py                # Entry point that launches the GUI
README.md              # This file
LICENSE                # License information
requirements.txt       # Python dependencies
core/                  # Core conversion and muxing logic
	ass_converter.py
	ffmpeg_locator.py
	muxer.py
	srt_converter.py
	subtitle_parser.py
gui/                   # GUI components (built with PyQt/PySide)
	drop_area.py
	log_panel.py
	main_window.py
	styles.py
	worker.py
utils/                 # Helper utilities
	encoding.py
	file_matcher.py
```

## Installation

```bash
# Install required Python packages
pip install -r requirements.txt

# (Optional) Download FFmpeg binaries
python download_ffmpeg.py

# Run the application
python main.py
```

## Usage

1. Launch the application with `python main.py`.
2. Drag video files and subtitle files onto the drop area.
3. Choose the desired output subtitle format (ASS or SRT).
4. Click **Convert** to generate the converted subtitle or **Mux** to embed it into the video.

## License

This project is licensed under the GPL-3.0 license – see the [LICENSE](LICENSE) file for details.
