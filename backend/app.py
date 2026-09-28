
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
# COOKIES
# ==========================================

# Cookies are optional.
#
# Render:
#   /etc/secrets/cookies.txt
#
# Local:
#   backend/cookies.txt
#
# IMPORTANT:
# Do NOT push your personal cookies.txt to GitHub.

COOKIE_CANDIDATES = [
    "/etc/secrets/cookies.txt",
    str(Path(__file__).resolve().parent / "cookies.txt"),
]

COOKIE_FILE = None

for candidate in COOKIE_CANDIDATES:
    if os.path.exists(candidate):
        COOKIE_FILE = candidate
        break


if COOKIE_FILE:
    print(f"[cookies] found: {COOKIE_FILE}")
else:
    print("[cookies] no cookies file found")


# ==========================================
# YOUTUBE DETECTION
# ==========================================

def is_youtube(url):
    """
    Check whether the URL belongs to YouTube.
    """

    if not url:
        return False

    url = url.lower().strip()

    return (
        "youtube.com" in url
        or "youtu.be" in url
        or "youtube-nocookie.com" in url
    )


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
# DOWNLOAD JOBS
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

    filename = re.sub(
        r'[<>:"/\\|?*]',
        "",
        filename
    )

    filename = re.sub(
        r'[\x00-\x1f]',
        "",
        filename
    )

    filename = filename.strip(" .")

    if not filename:

        filename = "social_video"

    return filename[:100]


# ==========================================
# YT-DLP OPTIONS
# ==========================================

def base_ydl_opts(
    quiet=True,
    url=None
):
    """
    Create the basic yt-dlp configuration.

    Cookies are used ONLY for YouTube.

    This means your YouTube cookies will not
    be sent to TikTok, Instagram, Facebook, etc.
    """

    opts = {

        "quiet": quiet,

        "no_warnings": quiet,

        "noplaylist": True,

        "cachedir": False,
    }


    # ======================================
    # YOUTUBE COOKIES ONLY
    # ======================================

    if COOKIE_FILE and url and is_youtube(url):

        opts["cookiefile"] = COOKIE_FILE

        print(
            "[cookies] YouTube cookies enabled"
        )

    else:

        if url and not is_youtube(url):

            print(
                "[cookies] non-YouTube URL - cookies disabled"
            )

    return opts


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():

    index_file = FRONTEND_DIR / "index.html"

    if index_file.exists():

        return FileResponse(
            str(index_file)
        )

    return {
        "message":
        "Social Video Downloader API is running"
    }


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
def health():

    return {

        "ok": True,

        "cookies": bool(COOKIE_FILE),

        "ffmpeg":
        imageio_ffmpeg.get_ffmpeg_exe()
    }


# ==========================================
# VIDEO INFO
# ==========================================

@app.post("/video-info")
def video_info(
    request: VideoRequest
):

    try:

        print("")
        print("==============================")
        print("VIDEO INFO REQUEST")
        print("==============================")

        print(
            "URL:",
            request.url
        )

        print(
            "YouTube:",
            is_youtube(request.url)
        )


        # ==================================
        # YT-DLP OPTIONS
        # ==================================

        ydl_opts = base_ydl_opts(
            quiet=True,
            url=request.url
        )


        # ==================================
        # EXTRACT INFO
        # ==================================

        with yt_dlp.YoutubeDL(
            ydl_opts
        ) as ydl:

            info = ydl.extract_info(
                request.url,
                download=False
            )


        # ==================================
        # FIND QUALITIES
        # ==================================

        qualities = set()

        for fmt in info.get(
            "formats",
            []
        ):

            height = fmt.get("height")

            if height:

                qualities.add(height)


        qualities = sorted(
            qualities,
            reverse=True
        )


        print(
            "VIDEO INFO SUCCESS"
        )

        print(
            "Title:",
            info.get("title")
        )

        print(
            "Qualities:",
            qualities
        )


        return {

            "success": True,

            "title":
            info.get("title"),

            "thumbnail":
            info.get("thumbnail"),

            "duration":
            info.get("duration"),

            "url":
            request.url,

            "qualities":
            qualities
        }


    except Exception as e:

        import traceback

        print("")
        print("==============================")
        print("VIDEO INFO ERROR")
        print("==============================")

        print(
            "ERROR TYPE:",
            type(e).__name__
        )

        print(
            "ERROR:",
            repr(e)
        )

        traceback.print_exc()


        # ==================================
        # CLEAN YOUTUBE ERROR
        # ==================================

        error_text = str(e)

        if is_youtube(request.url):

            if (
                "Sign in to confirm" in error_text
                or
                "not a bot" in error_text
                or
                "cookies" in error_text.lower()
            ):

                return {

                    "success": False,

                    "error":
                    "YouTube requires authentication for this video. "
                    "The server does not have valid YouTube cookies."
                }


        return {

            "success": False,

            "error":
            error_text
        }


# ==========================================
# START DOWNLOAD
# ==========================================

@app.post("/start-download")
def start_download(
    request: VideoRequest
):

    download_id = uuid.uuid4().hex


    filename = clean_filename(
        request.filename
    )


    job_folder = os.path.join(

        tempfile.gettempdir(),

        f"social_downloader_{download_id}"
    )


    os.makedirs(
        job_folder,
        exist_ok=True
    )


    # ======================================
    # CREATE DOWNLOAD JOB
    # ======================================

    downloads[download_id] = {

        "status":
        "starting",

        "progress":
        0,

        "speed":
        "0 B/s",

        "eta":
        None,

        "filename":
        f"{filename}.mp4",

        "folder":
        job_folder,

        "path":
        None,

        "error":
        None
    }


    # ======================================
    # START BACKGROUND THREAD
    # ======================================

    thread = threading.Thread(

        target=download_video,

        args=(

            download_id,

            request.url,

            request.quality,

            filename,

            job_folder
        )
    )


    thread.daemon = True

    thread.start()


    print("")
    print("==============================")
    print("DOWNLOAD JOB STARTED")
    print("==============================")

    print(
        "ID:",
        download_id
    )

    print(
        "Filename:",
        filename
    )

    print(
        "Quality:",
        request.quality
    )

    print(
        "YouTube:",
        is_youtube(request.url)
    )


    return {

        "success":
        True,

        "download_id":
        download_id
    }


# ==========================================
# DOWNLOAD VIDEO
# ==========================================

def download_video(

    download_id,

    url,

    quality,

    filename,

    job_folder
):

    try:

        # ==================================
        # FFMPEG
        # ==================================

        ffmpeg_path = (
            imageio_ffmpeg.get_ffmpeg_exe()
        )


        output_template = os.path.join(

            job_folder,

            "video.%(ext)s"
        )


        # ==================================
        # FORMAT
        # ==================================

        if quality == "best":

            video_format = (

                "bv*[ext=mp4]+ba[ext=m4a]/"

                "b[ext=mp4]/"

                "b"
            )

        else:

            video_format = (

                f"bv*[height<={quality}]"

                "[ext=mp4]+"

                "ba[ext=m4a]/"

                f"b[height<={quality}]"

                "[ext=mp4]/"

                "b"
            )


        # ==================================
        # PROGRESS HOOK
        # ==================================

        def progress_hook(data):

            status = data.get(
                "status"
            )


            # ==============================
            # DOWNLOADING
            # ==============================

            if status == "downloading":

                downloaded = data.get(
                    "downloaded_bytes",
                    0
                )


                total = (

                    data.get(
                        "total_bytes"
                    )

                    or

                    data.get(
                        "total_bytes_estimate"
                    )
                )


                if total and total > 0:

                    percent = round(

                        (
                            downloaded
                            /
                            total
                        )
                        *
                        100,

                        1
                    )

                else:

                    percent = 0


                downloads[
                    download_id
                ].update({

                    "status":
                    "downloading",

                    "progress":
                    percent,

                    "speed":
                    data.get(
                        "_speed_str",
                        "Calculating..."
                    ),

                    "eta":
                    data.get(
                        "eta"
                    )
                })


            # ==============================
            # DOWNLOAD FINISHED
            # ==============================

            elif status == "finished":

                downloads[
                    download_id
                ].update({

                    "status":
                    "processing",

                    "progress":
                    99,

                    "speed":
                    "",

                    "eta":
                    None
                })


                print(
                    "Download finished, processing..."
                )


        # ==================================
        # YT-DLP OPTIONS
        # ==================================

        ydl_opts = base_ydl_opts(

            quiet=False,

            url=url
        )


        ydl_opts.update({

            "format":
            video_format,

            "merge_output_format":
            "mp4",

            "outtmpl":
            output_template,

            "ffmpeg_location":
            ffmpeg_path,

            "progress_hooks":
            [
                progress_hook
            ]
        })


        # ==================================
        # UPDATE STATUS
        # ==================================

        downloads[
            download_id
        ]["status"] = "downloading"


        # ==================================
        # START YT-DLP
        # ==================================

        with yt_dlp.YoutubeDL(
            ydl_opts
        ) as ydl:

            ydl.download(
                [url]
            )


        # ==================================
        # FIND CREATED FILE
        # ==================================

        files = os.listdir(
            job_folder
        )


        print(
            "Files created:",
            files
        )


        mp4_files = [

            file

            for file in files

            if file.lower().endswith(
                ".mp4"
            )
        ]


        if not mp4_files:

            raise Exception(

                "yt-dlp finished but no MP4 "
                "file was found."
            )


        actual_file = os.path.join(

            job_folder,

            mp4_files[0]
        )


        final_path = os.path.join(

            job_folder,

            f"{filename}.mp4"
        )


        # ==================================
        # RENAME
        # ==================================

        os.replace(

            actual_file,

            final_path
        )


        # ==================================
        # COMPLETE
        # ==================================

        downloads[
            download_id
        ].update({

            "status":
            "completed",

            "progress":
            100,

            "path":
            final_path,

            "filename":
            f"{filename}.mp4",

            "speed":
            "",

            "eta":
            None
        })


        print("")
        print("==============================")
        print("DOWNLOAD SUCCESSFUL")
        print("==============================")


        print(
            "Final file:",
            final_path
        )


    except Exception as e:

        import traceback

        print("")
        print("==============================")
        print("DOWNLOAD ERROR")
        print("==============================")


        print(
            "ERROR TYPE:",
            type(e).__name__
        )


        print(
            "ERROR:",
            repr(e)
        )


        traceback.print_exc()


        # ==================================
        # CLEAN ERROR MESSAGE
        # ==================================

        error_message = str(e)


        if is_youtube(url):

            if (

                "Sign in to confirm"
                in error_message

                or

                "not a bot"
                in error_message

                or

                "cookies"
                in error_message.lower()
            ):

                error_message = (

                    "YouTube requires authentication "
                    "for this video. "
                    "The server does not have valid "
                    "YouTube cookies."
                )


        # ==================================
        # SAVE ERROR
        # ==================================

        downloads[
            download_id
        ].update({

            "status":
            "error",

            "error":
            error_message
        })


# ==========================================
# DOWNLOAD PROGRESS
# ==========================================

@app.get(
    "/download-progress/{download_id}"
)
def download_progress(
    download_id: str
):

    if download_id not in downloads:

        raise HTTPException(

            status_code=404,

            detail="Download not found"
        )


    return downloads[
        download_id
    ]


# ==========================================
# DOWNLOAD FINAL FILE
# ==========================================

@app.get(
    "/download-file/{download_id}"
)
def download_file(
    download_id: str
):

    if download_id not in downloads:

        raise HTTPException(

            status_code=404,

            detail="Download not found"
        )


    download = downloads[
        download_id
    ]


    if download["status"] != "completed":

        raise HTTPException(

            status_code=400,

            detail=
            "Download is not completed yet"
        )


    path = download["path"]


    if not path:

        raise HTTPException(

            status_code=404,

            detail="File path is missing"
        )


    if not os.path.exists(path):

        raise HTTPException(

            status_code=404,

            detail=
            "Video file does not exist"
        )


    print(
        "Sending file:",
        path
    )


    return FileResponse(

        path=path,

        media_type="video/mp4",

        filename=download[
            "filename"
        ]
    )

