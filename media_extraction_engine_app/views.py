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
def download_selected_video_view(request, format_id):
    video = request.session.get("current_video")
    if not video:
        return redirect("video-analyzer")

    url = video["url"]

    # Use a temporary folder to store downloads
    with tempfile.TemporaryDirectory() as tmpdirname:
        output_template = os.path.join(tmpdirname, "%(title)s.%(ext)s")

        # Sanitize filenames to remove problematic characters
        def sanitize_filename(d):
            if "title" in d:
                d["title"] = re.sub(r'[\\/*?:"<>|]', "_", d["title"])
            return d

        ydl_opts = {
            "format": format_id,
            "outtmpl": output_template,
            "quiet": True,
            "progress_hooks": [],
            "postprocessors_hooks": [],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                info = sanitize_filename(info)
                filename = ydl.prepare_filename(info)

            # Serve file to browser
            return FileResponse(open(filename, "rb"), as_attachment=True)

        except Exception as e:
            logger.exception(f"Download failed for {url} with format {format_id}")
            return HttpResponse(f"Download failed: {str(e)}", status=500)