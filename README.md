# Social Video Downloader

A lightweight web app for downloading social media videos from supported public URLs. The project combines a FastAPI backend, a small browser UI, and `yt-dlp` to fetch and convert media into downloadable files.

## Overview

This downloader lets users:

- paste a supported social video URL
- inspect available video qualities
- choose a preferred quality
- trigger a server-side download job
- receive the final MP4 file in the browser

## Features

- 🎥 Download video content from supported sites via `yt-dlp`
- 📱 Browser-based frontend with a simple HTML/CSS/JavaScript UI
- ⚡ FastAPI backend for reliable API handling
- 🎚️ Quality selection support based on available formats
- 📊 Download progress and job status tracking
- 📁 Temporary file handling per download session
- 🔄 FFmpeg-based media processing when required
- 🧩 Ready for local development and Docker-based deployment

## Tech Stack

### Backend

- Python 3.10+
- FastAPI
- Uvicorn
- yt-dlp
- curl-cffi
- imageio-ffmpeg

### Frontend

- HTML
- CSS
- JavaScript

### Media processing

- FFmpeg

## Project Structure

```text
social-video-downloader/
├── backend/
│   ├── app.py
│   ├── main.py
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── index.html
│   ├── css/
│   └── js/
├── .gitignore
├── .dockerignore
├── Dockerfile
├── pyproject.toml
├── README.md
└── .venv/   # local environment, not committed
```

## Project Metadata

The repository now includes a proper Python project definition in [pyproject.toml](pyproject.toml). It declares:

- project name and version
- description and keywords
- supported Python versions
- runtime dependencies
- build metadata for packaging and tooling

## Requirements

Before running the app, make sure the following are installed:

- Python 3.10 or newer
- FFmpeg
- Git
- Internet access for download requests

## Quick Start

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd social-video-downloader
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

You can also install the project metadata package in editable mode:

```bash
python -m pip install -e .
```

### 4. Run the API server

From the project root:

```bash
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

The app should be available at:

- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs

## Docker

A Dockerfile is included for containerized deployment.

```bash
docker build -t social-video-downloader .
docker run --rm -p 8000:8000 -e PORT=8000 social-video-downloader
```

## Environment Notes

If you need local secrets or browser cookies, keep them in a local `.env` file or a secure machine-specific location. Do not commit sensitive data to source control.

## Supported Platforms

Support depends on the upstream capabilities of `yt-dlp` and the hosting site. Some platforms may require updated extractor support or browser impersonation.

You can inspect extractor availability with:

```bash
python -m yt_dlp --list-extractors
```

## Testing the downloader

You can validate a URL directly with `yt-dlp` before using the app:

```bash
python -m yt_dlp "https://example.com/video-url"
```

For browser impersonation cases:

```bash
python -m yt_dlp --impersonate chrome "https://example.com/video-url"
```

## Important Usage Note

This project is intended to download content only when you have permission to do so. Users are responsible for following platform terms of service, copyright laws, and local regulations.

## Troubleshooting

### `yt-dlp` is not found

Use:

```bash
python -m yt_dlp --version
```

rather than relying on a global `yt-dlp` binary.

### FFmpeg is missing

Check it with:

```bash
ffmpeg -version
```

If it is not installed, install FFmpeg and ensure it is available in your system PATH.

## License

This project currently has no explicit repository license. If you plan to publish or distribute it publicly, add a license file and update the project metadata accordingly.
