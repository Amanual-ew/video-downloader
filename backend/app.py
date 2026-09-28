from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import yt_dlp
import imageio_ffmpeg

import tempfile
import os
import uuid
import threading
import re
from pathlib import Path


app = FastAPI()


# ==========================================
# PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


# ==========================================
# COOKIES (works locally and on Render)
# ==========================================

# On Render: set a Secret File mounted at /etc/secrets/cookies.txt
# Locally: put cookies.txt in the backend folder (optional)

COOKIE_CANDIDATES = [
    "/etc/secrets/cookies.txt",                      # Render secret file
    str(Path(__file__).resolve().parent / "cookies.txt"),  # local backend/cookies.txt
]

COOKIE_FILE = None
for candidate in COOKIE_CANDIDATES:
    if os.path.exists(candidate):
        COOKIE_FILE = candidate
        break

if COOKIE_FILE:
    print(f"[cookies] using {COOKIE_FILE}")
else:
    print("[cookies] no cookies file found — some sites may fail")


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# SERVE FRONTEND
# ==========================================

if FRONTEND_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(FRONTEND_DIR)),
        name="static"
    )


# ==========================================
# STORE DOWNLOAD JOBS
# ==========================================

downloads = {}


# ==========================================
# REQUEST MODEL
# ==========================================

class VideoRequest(BaseModel):
    url: str
    quality: str = "best"
    filename: str = "social_video"


# ==========================================
# SAFE FILE NAME
# ==========================================

def clean_filename(filename):

    filename = filename.strip()

    if not filename:
        filename = "social_video"

    if filename.lower().endswith(".mp4"):
        filename = filename[:-4]

    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    filename = re.sub(r'[\x00-\x1f]', "", filename)
    filename = filename.strip(" .")

    if not filename:
        filename = "social_video"

    return filename[:100]


# ==========================================
# SHARED YT-DLP BASE OPTIONS
# ==========================================

def base_ydl_opts(quiet=True):
    opts = {
        "quiet": quiet,
        "no_warnings": quiet,
        "noplaylist": True,
        # Make requests look like a real Chrome browser.
        # This is the main fix for TikTok/Instagram on Render.
        "impersonate": "chrome",
        # Don't let yt-dlp try to write into read-only places
        "cachedir": False,
    }
    if COOKIE_FILE:
        opts["cookiefile"] = COOKIE_FILE
    return opts


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():

    index_file = FRONTEND_DIR / "index.html"

    if index_file.exists():
        return FileResponse(str(index_file))

    return {"message": "Social Video Downloader API is running"}


# ==========================================
# HEALTH (useful for Render)
# ==========================================

@app.get("/health")
def health():
    return {
        "ok": True,
        "cookies": bool(COOKIE_FILE),
        "ffmpeg": imageio_ffmpeg.get_ffmpeg_exe(),
    }


# ==========================================
# VIDEO INFO
# ==========================================

@app.post("/video-info")
def video_info(request: VideoRequest):

    try:

        ydl_opts = base_ydl_opts(quiet=True)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)

        qualities = set()
        for fmt in info.get("formats", []):
            height = fmt.get("height")
            if height:
                qualities.add(height)

        qualities = sorted(qualities, reverse=True)

        return {
            "success": True,
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "url": request.url,
            "qualities": qualities,
        }

    except Exception as e:
        import traceback

        print("[video-info] ERROR:", repr(e))
        traceback.print_exc()

        return {
            "success": False,
            "error": repr(e)
        }


# ==========================================
# START DOWNLOAD
# ==========================================

@app.post("/start-download")
def start_download(request: VideoRequest):

    download_id = uuid.uuid4().hex
    filename = clean_filename(request.filename)

    job_folder = os.path.join(
        tempfile.gettempdir(),
        f"social_downloader_{download_id}"
    )
    os.makedirs(job_folder, exist_ok=True)

    downloads[download_id] = {
        "status": "starting",
        "progress": 0,
        "speed": "0 B/s",
        "eta": None,
        "filename": f"{filename}.mp4",
        "folder": job_folder,
        "path": None,
        "error": None,
    }

    thread = threading.Thread(
        target=download_video,
        args=(download_id, request.url, request.quality, filename, job_folder)
    )
    thread.daemon = True
    thread.start()

    print("=" * 30)
    print("DOWNLOAD JOB STARTED:", download_id)
    print("Filename:", filename, "| Quality:", request.quality)

    return {"success": True, "download_id": download_id}


# ==========================================
# DOWNLOAD VIDEO
# ==========================================

def download_video(download_id, url, quality, filename, job_folder):

    try:

        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

        output_template = os.path.join(job_folder, "video.%(ext)s")

        if quality == "best":
            video_format = (
                "bv*[ext=mp4]+ba[ext=m4a]/"
                "b[ext=mp4]/"
                "b"
            )
        else:
            video_format = (
                f"bv*[height<={quality}][ext=mp4]+ba[ext=m4a]/"
                f"b[height<={quality}][ext=mp4]/"
                "b"
            )

        def progress_hook(data):

            status = data.get("status")

            if status == "downloading":

                downloaded = data.get("downloaded_bytes", 0)
                total = data.get("total_bytes") or data.get("total_bytes_estimate")

                if total and total > 0:
                    percent = round((downloaded / total) * 100, 1)
                else:
                    percent = 0

                downloads[download_id].update({
                    "status": "downloading",
                    "progress": percent,
                    "speed": data.get("_speed_str", "Calculating..."),
                    "eta": data.get("eta"),
                })

            elif status == "finished":

                downloads[download_id].update({
                    "status": "processing",
                    "progress": 99,
                    "speed": "",
                    "eta": None,
                })
                print("Download finished, processing...")

        ydl_opts = base_ydl_opts(quiet=False)
        ydl_opts.update({
            "format": video_format,
            "merge_output_format": "mp4",
            "outtmpl": output_template,
            "ffmpeg_location": ffmpeg_path,
            "progress_hooks": [progress_hook],
        })

        downloads[download_id]["status"] = "downloading"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        files = os.listdir(job_folder)
        print("Files created:", files)

        mp4_files = [f for f in files if f.lower().endswith(".mp4")]

        if not mp4_files:
            raise Exception("yt-dlp finished but no MP4 file was found.")

        actual_file = os.path.join(job_folder, mp4_files[0])
        final_path = os.path.join(job_folder, f"{filename}.mp4")

        os.replace(actual_file, final_path)

        downloads[download_id].update({
            "status": "completed",
            "progress": 100,
            "path": final_path,
            "filename": f"{filename}.mp4",
            "speed": "",
            "eta": None,
        })

        print("DOWNLOAD SUCCESSFUL:", final_path)

    except Exception as e:

        print("DOWNLOAD ERROR:", str(e))

        downloads[download_id].update({
            "status": "error",
            "error": str(e),
        })


# ==========================================
# PROGRESS
# ==========================================

@app.get("/download-progress/{download_id}")
def download_progress(download_id: str):

    if download_id not in downloads:
        raise HTTPException(status_code=404, detail="Download not found")

    return downloads[download_id]


# ==========================================
# DOWNLOAD FINAL FILE
# ==========================================

@app.get("/download-file/{download_id}")
def download_file(download_id: str):

    if download_id not in downloads:
        raise HTTPException(status_code=404, detail="Download not found")

    download = downloads[download_id]

    if download["status"] != "completed":
        raise HTTPException(status_code=400, detail="Download is not completed yet")

    path = download["path"]

    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Video file does not exist")

    print("Sending file:", path)

    return FileResponse(
        path=path,
        media_type="video/mp4",
        filename=download["filename"],
    )