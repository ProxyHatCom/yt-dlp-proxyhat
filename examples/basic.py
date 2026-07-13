"""Minimal yt-dlp + ProxyHat example: unblock a region-locked video.

    PROXYHAT_API_KEY=ph_xxx python examples/basic.py

The whole download runs through a US residential IP, pinned for the run (sticky
by default), so yt-dlp fetches the manifest and every fragment from the same
country — the reliable way past geo-restrictions.
"""

from yt_dlp_proxyhat import ProxyHatYoutubeDL

URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def main() -> None:
    # api_key defaults to PROXYHAT_API_KEY and auto-selects an active sub-user.
    with ProxyHatYoutubeDL({"format": "best"}, country="us") as ydl:
        print("routing through:", ydl.proxyhat_url)
        ydl.download([URL])


if __name__ == "__main__":
    main()
