import yt_dlp


def extract_video_metadata(url: str):
    """
    Extracts video metadata without downloading.
    Returns:
        {
            "title": str,
            "thumbnail": str,
            "duration": int (seconds),
            "formats": list of available formats,
        }
    """
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "forcejson": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = []
    for f in info.get("formats", []):
        # Only include video or audio streams
        if f.get("vcodec") != "none" or f.get("acodec") != "none":
            formats.append({
                "format_id": f.get("format_id"),
                "ext": f.get("ext"),
                "resolution": f.get("resolution") or f.get("height"),
                "note": f.get("format_note"),
            })

    return {
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "formats": formats,
    }