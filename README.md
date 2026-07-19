# YouTube Playlist Downloader

A desktop application for downloading entire YouTube playlists (or selected videos from them) with a clean, modern GUI. Built with Python, [`customtkinter`](https://github.com/TomSchimansky/CustomTkinter) for the interface, [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) for downloading, and SQLite for download history.

---

## Table of Contents

- [Features](#features)
- [Screenshots / Layout](#screenshots--layout)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [How to Use](#how-to-use)
- [Configuration (settings.json)](#configuration-settingsjson)
- [Download History](#download-history)
- [Testing](#testing)
- [Building / Packaging](#building--packaging)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

- **Playlist Analysis** — Paste a YouTube playlist URL and the app fetches all videos using `yt-dlp` (title, duration, thumbnail, and an estimated file size for the chosen resolution).
- **Selective Downloads** — Each video has a checkbox so you can download only the videos you want. Already-downloaded videos are detected from history, marked, and auto-deselected (but can be re-selected to re-download).
- **Quality Selection** — Choose between `1080p`, `720p`, or `Best Available`. The format string is resolved automatically (`bestvideo[height<=N]+bestaudio` merged to MP4).
- **MP4 Output** — Downloads are merged and converted to MP4 using FFmpeg (`FFmpegVideoConvertor` postprocessor).
- **Pause / Resume / Skip / Cancel** — Full control over an in-progress download run:
  - **Pause** / **Resume** the current download.
  - **Skip** the current video and move to the next one.
  - **Cancel** the entire queue.
- **Live Progress Tracking** — Two progress bars:
  - **Current Video** — percentage, download speed, and time remaining (ETA) for the active video.
  - **Whole Playlist** — size-weighted progress (larger videos advance the bar more), total downloaded vs. total size, and an estimated time left for the whole playlist.
- **Resumable Queue** — Unfinished downloads are stored in a `download_queue` table. On launch, the app detects pending downloads and asks whether to resume them.
- **Download History** — A dedicated History window shows every downloaded video (title, URL, saved path, date, and status) stored in a local SQLite database.
- **Theming** — Light / Dark / System appearance modes via `customtkinter`, applied automatically from saved settings.
- **Persistent Settings** — Download folder, quality, theme, last playlist URL, and max threads are saved to `settings.json`.
- **FFmpeg Check** — On startup the app verifies FFmpeg is available and warns the user if it is missing (needed for best-quality merging).
- **Activity Log** — A built-in log panel shows real-time status messages.
- **Organized Output** — Videos are saved under `Download Folder/YouTube Downloads/<Playlist Title>/`.
- **Robust Downloads** — Uses `continuedl` (resume partial files), `restrictfilenames` (clean filenames), and skips invalid Windows filename characters.

---

## Screenshots / Layout

The main window is split into:

- **Sidebar** (left) — Navigation buttons: *Analyze / Downloader* and *History*.
- **Main Area** (right, scrollable):
  1. **Playlist URL** input + **Quality** dropdown + *Fetch Playlist* button.
  2. **Download Folder** input + *Browse* button.
  3. **Playlist Content** list — checkbox, thumbnail, title, duration, estimated size, downloaded status, and per-video status.
  4. **Start All Downloads** button.
  5. **Activity & Progress** — status line, current-video progress, playlist progress, speed/ETA labels, Pause/Resume/Skip/Cancel controls, and a log box.

---

## Project Structure

```
.
├── app.py                  # Application entry point (launches MainWindow)
├── requirements.txt        # Python dependencies
├── settings.json           # Persisted user settings (auto-created)
├── core/                   # Backend logic
│   ├── __init__.py
│   ├── database.py         # SQLite manager (history + resume queue)
│   ├── downloader.py       # yt-dlp download engine + pause/skip/cancel
│   ├── playlist.py         # PlaylistAnalyzer + VideoInfo/PlaylistInfo
│   ├── queue_manager.py    # In-memory download queue
│   ├── settings.py         # SettingsManager (JSON-backed)
│   ├── system_check.py     # FFmpeg availability check
│   ├── utils.py            # Formatting + thumbnail helpers
│   ├── models.py           # (reserved / empty)
│   ├── worker.py           # (reserved / empty)
│   └── logger.py           # (reserved / empty)
├── gui/                    # CustomTkinter UI
│   ├── main_window.py      # Main application window
│   ├── settings_window.py  # Settings dialog
│   ├── history_window.py   # Download history table
│   ├── sidebar.py          # Navigation sidebar
│   └── widgets.py          # Reusable UI widgets (SectionFrame, StatusCard)
├── database/               # SQLite database files (history.db)
├── downloads/              # Default/example download output
├── assets/                 # Application assets
├── build/                  # Build/packaging output (empty by default)
├── logs/                   # Log output
└── test_*.py               # Manual test scripts (db, downloader, playlist, settings)
```

---

## Requirements

- **Python** 3.10 or newer (uses `int | None` style type hints).
- **FFmpeg** installed and available on your system `PATH` (required for merging/convert to MP4). Download from <https://ffmpeg.org/download.html>.
- The Python packages listed in `requirements.txt`:
  - `customtkinter==6.0.0`
  - `darkdetect==0.8.0`
  - `packaging==26.2`
  - `pillow==12.3.0`
  - `yt-dlp==2026.7.4`
  - `requests==2.34.2`

> **Note:** `sqlite3` is part of the Python standard library, so no extra install is needed for the database.

---

## Installation

1. **Clone or download** this repository and open the project folder:

   ```powershell
   cd "d:\Projects\Youtube Playlist downloader"
   ```

2. **(Recommended) Create and activate a virtual environment:**

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   > If PowerShell blocks the script, run:
   > `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`

3. **Install dependencies:**

   ```powershell
   pip install -r requirements.txt
   ```

4. **Install FFmpeg** (if not already present) and ensure `ffmpeg` is reachable from the command line:

   ```powershell
   ffmpeg -version
   ```

---

## Running the Application

From the project root (with the virtual environment activated):

```powershell
python app.py
```

The main window will open. If FFmpeg is not detected, a warning dialog appears — downloads will still work for some formats, but MP4 merging at higher quality requires FFmpeg.

---

## How to Use

1. **Set the download folder** — Click *Browse* (or it uses the saved default from `settings.json`).
2. **Choose a quality** — Pick `1080p`, `720p`, or `Best Available` from the dropdown. This enables the *Fetch Playlist* button.
3. **Paste a playlist URL** — e.g. `https://www.youtube.com/playlist?list=...` and click *Fetch Playlist*.
4. **Review the list** — Thumbnails, titles, durations, and estimated sizes appear. Tick/untick videos to select what to download. Already-downloaded items are marked and deselected automatically.
5. **Start the download** — Click *Start All Downloads*.
6. **Control the run:**
   - **Pause** / **Resume** — freeze or continue the active download.
   - **Skip** — abandon the current video and continue with the next.
   - **Cancel** — stop the entire queue.
7. **Watch progress** — The current-video and whole-playlist progress bars, speed, and ETAs update live. A log panel records activity.
8. **View history** — Click *History* in the sidebar to open the download history table.
9. **Resume later** — If you close the app mid-download, pending items are saved. On the next launch you'll be asked to resume them.

---

## Configuration (settings.json)

Settings are stored in `settings.json` at the project root and created automatically with defaults on first run. Example:

```json
{
    "download_folder": "D:/Channels",
    "quality": "1080p",
    "theme": "Dark",
    "last_playlist": "https://www.youtube.com/playlist?list=PLxSiKKDbuUTua4oFVFed_RXPcsboA4Myo",
    "max_threads": 3
}
```

| Key              | Description                                                        | Default        |
| ---------------- | ------------------------------------------------------------------ | -------------- |
| `download_folder`| Default folder where videos are saved.                             | `""` (empty)   |
| `quality`        | Default download quality (`1080p`, `720p`, `Best Available`).      | `1080p`        |
| `theme`          | UI theme: `dark`, `light`, or `system`.                            | `dark`         |
| `last_playlist`  | Last used playlist URL (pre-filled on launch).                    | `""`           |
| `max_threads`    | Reserved for concurrency tuning.                                  | `3`            |

> The Settings window (`gui/settings_window.py`) lets you change these from the UI; changes persist to `settings.json`.

---

## Download History

- Stored in `database/history.db` (SQLite).
- The **History** window lists every recorded download with columns: *Title, URL, Path, Date, Status*.
- The same database keeps a `download_queue` table used to resume interrupted downloads.

---

## Testing

The repository includes manual test scripts at the root. They are run directly (not as a test framework) and print results to the console:

```powershell
python test_db.py          # Verifies the database is created and counts downloads
python test_settings.py    # Reads/updates settings via SettingsManager
python test_playlist.py    # Prompts for a playlist URL and prints its title
python test_downloader.py  # Attempts a real download of a sample video
```

> `test_downloader.py` performs an actual network download, so use it with care.

---

## Building / Packaging

The `build/` directory is provided for packaging output (e.g., with PyInstaller). A typical one-folder build:

```powershell
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed app.py
```

Adjust the spec as needed to bundle `settings.json` and the `core`/`gui` packages.

---

## Troubleshooting

- **"FFmpeg Missing" warning** — Install FFmpeg and add it to your `PATH`, then restart the app.
- **Fetch button disabled** — You must select a quality from the dropdown first.
- **Download fails / no progress** — Check your internet connection and that the playlist URL is public/accessible; `yt-dlp` may need updating (`pip install -U yt-dlp`).
- **Already-downloaded videos reappear** — They are shown so you can re-download if the files were deleted; simply leave them unchecked to skip.
- **Database locked errors** — The `DatabaseManager` uses a thread lock and `check_same_thread=False`; avoid opening the DB from multiple separate processes simultaneously.

---

## License

This project is provided as-is for personal, educational use. Respect YouTube's Terms of Service and applicable copyright laws when downloading content.
