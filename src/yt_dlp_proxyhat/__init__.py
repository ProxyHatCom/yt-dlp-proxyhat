"""yt-dlp-proxyhat — download videos with yt-dlp through ProxyHat residential proxies."""

from typing import Any

from yt_dlp_proxyhat._resolve import ProxyHatConfigError, resolve_credentials
from yt_dlp_proxyhat.proxy import proxyhat_proxy_url, proxyhat_ydl_opts

__all__ = [
    "ProxyHatConfigError",
    "ProxyHatYoutubeDL",
    "proxyhat_proxy_url",
    "proxyhat_ydl_opts",
    "resolve_credentials",
]
__version__ = "0.1.0"


def __getattr__(name: str) -> Any:
    # Re-export the lazily-built subclass so `from yt_dlp_proxyhat import
    # ProxyHatYoutubeDL` works without importing yt-dlp at package import time.
    if name == "ProxyHatYoutubeDL":
        from yt_dlp_proxyhat.proxy import ProxyHatYoutubeDL

        return ProxyHatYoutubeDL
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
