# Social Video Downloader

A web-based video downloader built with **FastAPI** and **yt-dlp**.
The application allows users to enter a supported social-media video URL, choose a video quality, download the video, and receive the downloaded file.

## Features

* 🎥 Download online videos
* 📱 Support for multiple platforms through `yt-dlp`
* 🎚️ Video quality selection
* 📊 Download progress percentage
* ⏳ Download status messages
* 📁 Temporary server-side file handling
* ⚡ FastAPI backend
* 🔄 Automatic video/audio merging with FFmpeg when required
* 🖥️ Simple web interface

## Technologies Used

### Backend

* Python
* FastAPI
* Uvicorn
* yt-dlp
* curl-cffi

### Media Processing

* FFmpeg

### Frontend

* HTML
* CSS
* JavaScript

## Project Structure

```text
social-video-downloader/
│
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   └── ...
│
├── README.md
└── ...
```

> The exact structure may be different depending on your current project files.

## Requirements

Before running the project, make sure you have:

* Python 3.10+
* FFmpeg
* Git
* Internet connection

## Installation

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd social-video-downloader
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
```

Activate it:

```powershell
venv\Scripts\activate
```

### 3. Install Python dependencies

```powershell
pip install -r backend/requirements.txt
```

## Running the Backend

Go to the backend directory:

```powershell
cd backend
```

Start the FastAPI server:

```powershell
python -m uvicorn app:app --reload
```

The API will normally be available at:

```text
http://127.0.0.1:8000
```

FastAPI documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Testing yt-dlp

You can test `yt-dlp` directly from the terminal:

```powershell
python -m yt_dlp "VIDEO_URL"
```

For example:

```powershell
python -m yt_dlp "https://www.tiktok.com/@username/video/VIDEO_ID"
```

If your system requires browser impersonation:

```powershell
python -m yt_dlp --impersonate chrome "VIDEO_URL"
```

## Environment Variables

If the project requires environment variables, create a `.env` file locally.

Example:

```env
PORT=8000
```

Do **not** upload passwords, API keys, cookies, or other secrets to GitHub.

Add `.env` to `.gitignore`:

```text
.env
venv/
__pycache__/
*.pyc
downloads/
```

## Supported Platforms

Platform support depends on the current capabilities of `yt-dlp`. Supported websites can change over time.

You can check the current extractor list with:

```powershell
python -m yt_dlp --list-extractors
```

Some websites may require additional configuration or may temporarily stop working when the website changes its systems.

## Deployment

The application can be deployed to a cloud platform that supports Python/FastAPI applications.

For production, the application should be started with:

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

FFmpeg must also be available on the deployment server if the application needs to merge video and audio streams.

## Important Notes

This project is intended for downloading content that you have permission to download.

Users are responsible for following the terms of service and copyright laws applicable to the content and websites they use.

The availability of a website through `yt-dlp` does not guarantee that every video will always be downloadable.

## Troubleshooting

### `yt-dlp` is not recognized

Use:

```powershell
python -m yt_dlp --version
```

instead of:

```powershell
yt-dlp --version
```

Install or update it with:

```powershell
python -m pip install -U yt-dlp
```

### TikTok download fails

First update the dependencies:

```powershell
python -m pip install -U yt-dlp
python -m pip install -U curl-cffi
```

Then test:

```powershell
python -m yt_dlp --impersonate chrome "TIKTOK_URL"
```

### FFmpeg error

Make sure FFmpeg is installed and available in your system PATH.

Check it with:

```powershell
ffmpeg -version
```

## Future Improvements

* User download history
* Better error messages
* More platform support
* Download cancellation
* Improved mobile interface
* Background download jobs
* Cloud storage integration
* Production deployment

## License

This project is for educational and personal development purposes.
