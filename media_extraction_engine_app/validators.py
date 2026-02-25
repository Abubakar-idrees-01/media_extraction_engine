from urllib.parse import urlparse

SUPPORTED_DOMAINS = {
    "youtube": ["youtube.com", "youtu.be"],
    "instagram": ["instagram.com"],
    "tiktok": ["tiktok.com", "vm.tiktok.com", "vt.tiktok.com"],
}


def analyze_video_source(url: str):
    """
    Determines which platform the provided URL belongs to.
    More strict validation for hostname to prevent fake links.
    """

    try:
        parsed = urlparse(url)
        hostname = parsed.netloc.lower()

        if not hostname:
            return {
                "is_valid": False,
                "platform": None,
                "message": "Invalid URL format"
            }

        for platform, domains in SUPPORTED_DOMAINS.items():
            for domain in domains:
                # Strict match: exact or subdomain
                if hostname == domain or hostname.endswith("." + domain):
                    return {
                        "is_valid": True,
                        "platform": platform,
                        "message": "Platform detected"
                    }

        return {
            "is_valid": False,
            "platform": None,
            "message": "Platform not supported"
        }

    except Exception:
        return {
            "is_valid": False,
            "platform": None,
            "message": "Invalid URL."
        }