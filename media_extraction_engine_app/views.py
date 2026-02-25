# media_extraction_engine_app/views.py

from django.shortcuts import render, redirect
from django.http import HttpResponse
from .validators import analyze_video_source
from .services.metadata_extractor import extract_video_metadata
import logging
import os

logger = logging.getLogger(__name__)

# ------------------------------
# Step 1: Analyze Video URL
# ------------------------------
def video_source_analysis_view(request):
    """
    Receives video URL from user, validates platform,
    and stores basic info in session for next step.
    """
    context = {}

    if request.method == "POST":
        user_url = request.POST.get("video_url")
        result = analyze_video_source(user_url)
        context["result"] = result
        context["video_url"] = user_url

        if result["is_valid"]:
            # Store temporary data in session
            request.session["current_video"] = {
                "url": user_url,
                "platform": result["platform"]
            }

    return render(request, "media_extraction_engine_app/video_analyzer.html", context)


# ------------------------------
# Step 2: Video Quality Selection
# ------------------------------
def quality_selection_redirect_view(request):
    """
    Redirects user to quality selection page,
    fetches video metadata, stores it in session object.
    """
    video = request.session.get("current_video")
    if not video:
        return redirect("video-analyzer")

    # Extract metadata using yt-dlp
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
    """
    Downloads the selected format (quality) using yt-dlp,
    stores file temporarily in media/downloads, and sends to user.
    """
    video = request.session.get("current_video")
    if not video:
        return redirect("video-analyzer")

    url = video["url"]

    # Ensure downloads folder exists
    download_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "media", "downloads")
    os.makedirs(download_folder, exist_ok=True)

    # Build yt-dlp options
    output_path = os.path.join(download_folder, "%(title)s.%(ext)s")
    ydl_opts = {
        "format": format_id,
        "outtmpl": output_path,
        "quiet": True,
    }

    import yt_dlp

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # Send file to user
        from django.http import FileResponse

        response = FileResponse(open(filename, "rb"), as_attachment=True)
        return response

    except Exception as e:
        logger.exception(f"Download failed for {url} with format {format_id}")
        return HttpResponse(f"Download failed: {str(e)}", status=500)