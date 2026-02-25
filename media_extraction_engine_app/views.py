# media_extraction_engine_app/views.py

from django.shortcuts import render, redirect
from django.http import FileResponse, HttpResponse
from .validators import analyze_video_source
from .services.metadata_extractor import extract_video_metadata
import logging
import os
import yt_dlp
import re
import tempfile

logger = logging.getLogger(__name__)

# ------------------------------
# Step 1: Analyze Video URL
# ------------------------------
def video_source_analysis_view(request):
    context = {}

    if request.method == "POST":
        user_url = request.POST.get("video_url")
        result = analyze_video_source(user_url)
        context["result"] = result
        context["video_url"] = user_url

        if result["is_valid"]:
            # Store in session
            request.session["current_video"] = {
                "url": user_url,
                "platform": result["platform"]
            }
            # Redirect to quality selection (PRG pattern)
            return redirect("quality-selection")

    return render(request, "media_extraction_engine_app/video_analyzer.html", context)


# ------------------------------
# Step 2: Video Quality Selection
# ------------------------------
def quality_selection_redirect_view(request):
    video = request.session.get("current_video")
    if not video:
        return redirect("video-analyzer")

    try:
        metadata = extract_video_metadata(video["url"])
        video["metadata"] = metadata
    except Exception as e:
        logger.exception(f"Metadata extraction failed for {video['url']}")
        video["metadata"] = {"error": str(e)}

    return render(
        request,
        "media_extraction_engine_app/video_quality_selection.html",
        {"video": video}
    )


# ------------------------------
# Step 3: Download Selected Video
# ------------------------------
import os
import yt_dlp
import uuid
import shutil
import threading
from django.shortcuts import redirect
from django.http import FileResponse, HttpResponse

def download_selected_video_view(request, format_id):
    video = request.session.get("current_video")
    if not video:
        return redirect("video-analyzer")

    url = video["url"]

    # Create unique temporary folder
    base_download = os.path.join(os.path.dirname(os.path.dirname(__file__)), "media", "downloads")
    os.makedirs(base_download, exist_ok=True)
    tmp_dir = os.path.join(base_download, str(uuid.uuid4()))
    os.makedirs(tmp_dir, exist_ok=True)

    output_template = os.path.join(tmp_dir, "%(title)s.%(ext)s")

    # Change your ydl_opts to this:
    ydl_opts = {
        # 'best' tells yt-dlp to pick a single file that has BOTH video and audio
        # instead of picking the best video and best audio separately.
        "format": "best", 
        "outtmpl": output_template,
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # Get the actual downloaded file path
            if "requested_downloads" in info and len(info["requested_downloads"]) > 0:
                downloaded_file = info["requested_downloads"][0]["filepath"]
            else:
                # fallback
                downloaded_file = ydl.prepare_filename(info)

        # Serve the file
        response = FileResponse(open(downloaded_file, "rb"), as_attachment=True)

        # Schedule deletion of folder after 10 seconds
        def delete_later(path):
            import time
            time.sleep(10)
            shutil.rmtree(path, ignore_errors=True)

        threading.Thread(target=delete_later, args=(tmp_dir,), daemon=True).start()

        return response

    except Exception as e:
        return HttpResponse(f"Download failed: {str(e)}", status=500)