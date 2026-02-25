import yt_dlp

def extract_video_metadata(url: str):
    # We use a specific format selector that looks for combined files only
    # 'best' is the keyword for the best single file with video+audio
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "format": "best", 
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = []
    
    # Check if 'formats' exists; if not, yt-dlp might have just returned the 'best' one
    raw_formats = info.get("formats", [info])

    for f in raw_formats:
        v_codec = f.get("vcodec", "none")
        a_codec = f.get("acodec", "none")
        
        # Look for any format that isn't split (must have both codecs)
        if v_codec != "none" and a_codec != "none":
            height = f.get("height")
            res_label = f"{height}p" if height else "Standard Quality"
            
            formats.append({
                "format_id": f.get("format_id"),
                "ext": f.get("ext", "mp4"),
                "resolution": res_label,
                "note": f.get("format_note") or "Combined (Video + Audio)",
            })

    # If the list is STILL empty, we force-add the 'best' format yt-dlp found
    if not formats:
        formats.append({
            "format_id": "best",
            "ext": info.get("ext", "mp4"),
            "resolution": f"{info.get('height', 'Default')}p",
            "note": "Optimized Combined Format",
        })

    return {
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "formats": formats,
    }