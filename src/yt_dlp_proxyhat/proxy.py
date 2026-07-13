"""Route yt-dlp downloads through the ProxyHat residential gateway.

yt-dlp takes a single proxy per run — ``--proxy URL`` on the CLI, or the ``proxy``
key inside the ``YoutubeDL(params={...})`` dict in the Python API. This module
turns your ProxyHat credentials + geo-targeting into that URL with the official
``proxyhat`` SDK's grammar, so a whole download runs through a residential IP —
the main use being to **unblock region-locked videos** by exiting from a
residential IP in the right country.

- :func:`proxyhat_proxy_url` → the gateway URL for ``yt-dlp --proxy "$(...)"``.
- :func:`proxyhat_ydl_opts` → ``{"proxy": url, **base}`` to hand to ``YoutubeDL(...)``.
- :class:`ProxyHatYoutubeDL` → a thin ``yt_dlp.YoutubeDL`` subclass that injects
  the proxy for you (``yt_dlp`` is imported lazily, so importing this module is
  cheap and needs no yt-dlp install).

**Per-run, not per-fragment.** yt-dlp uses one proxy for the whole run, so
"rotation" here means a *fresh residential IP per run/connection*, never a new IP
mid-download. For geo-unblocking you almost always want the default (**sticky**):
one pinned IP for the entire download, which keeps the video manifest and its
fragments coming from the same country.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from proxyhat import build_connection_url

from yt_dlp_proxyhat._resolve import resolve_credentials

if TYPE_CHECKING:
    from yt_dlp import YoutubeDL

# Sticky by default: pin one residential IP for the whole download so the video
# manifest and every fragment exit from the same country. Override with any TTL
# string ("2h") or turn off with sticky=False to get a fresh IP per run.
DEFAULT_STICKY = "30m"


def proxyhat_proxy_url(
    *,
    api_key: str | None = None,
    username: str | None = None,
    password: str | None = None,
    sub_user: str | None = None,
    country: str | None = None,
    region: str | None = None,
    city: str | None = None,
    sticky: bool | str | None = DEFAULT_STICKY,
    filter: str | None = None,
    protocol: str = "http",
) -> str:
    """Build a ProxyHat gateway proxy URL for yt-dlp.

    Resolves credentials (an ``api_key`` auto-picks an active sub-user, or pass
    ``username``/``password``) and returns a URL like
    ``http://<user>-country-us-sid-<id>-ttl-30m:<pass>@gate.proxyhat.com:8080``.
    Pass it to ``yt-dlp --proxy "$(...)"`` on the CLI, to the ``proxy`` key of a
    ``YoutubeDL`` params dict, or let :func:`proxyhat_ydl_opts` /
    :class:`ProxyHatYoutubeDL` wire it for you.

    Geo-unblocking: set ``country`` to the region the video is available in (ISO
    code, e.g. ``"us"``, ``"gb"``, ``"jp"``) so yt-dlp fetches it through a
    residential IP there. ``region``, ``city`` and ``filter`` (AI IP-quality
    tier) narrow it further.

    Sticky vs rotating (per run — yt-dlp uses one proxy per run):

    - ``sticky="30m"`` (default) or ``sticky=True`` pins one residential IP for
      the whole download — recommended, keeps the manifest and its fragments
      coming from one country.
    - ``sticky=False`` (or ``None``) rotates: a fresh residential IP on the next
      run/connection, not mid-download.
    - ``sticky="2h"`` sets a custom session lifetime.

    ``protocol`` is ``"http"`` (default) or ``"socks5"`` (yt-dlp speaks both).
    """
    user, pw = resolve_credentials(
        api_key=api_key,
        username=username,
        password=password,
        sub_user=sub_user,
    )
    return build_connection_url(
        username=user,
        password=pw,
        country=country,
        region=region,
        city=city,
        sticky=sticky,
        filter=filter,
        protocol=protocol,
    )


def proxyhat_ydl_opts(
    *,
    api_key: str | None = None,
    username: str | None = None,
    password: str | None = None,
    sub_user: str | None = None,
    country: str | None = None,
    region: str | None = None,
    city: str | None = None,
    sticky: bool | str | None = DEFAULT_STICKY,
    filter: str | None = None,
    protocol: str = "http",
    base: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a ``YoutubeDL`` options dict with the ProxyHat ``proxy`` injected.

    Merge-friendly: any ``base`` options you already use (``format``,
    ``outtmpl``, ``geo_bypass``, …) are copied through, and the ProxyHat
    ``proxy`` URL is set on top (so it wins over a ``proxy`` in ``base`` — that
    is the whole point of this helper). Hand the result straight to
    ``yt_dlp.YoutubeDL(...)``::

        import yt_dlp
        from yt_dlp_proxyhat import proxyhat_ydl_opts

        opts = proxyhat_ydl_opts(country="us", base={"format": "bestvideo+bestaudio"})
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download(["https://www.youtube.com/watch?v=..."])

    Accepts the same credential + targeting arguments as
    :func:`proxyhat_proxy_url`.
    """
    url = proxyhat_proxy_url(
        api_key=api_key,
        username=username,
        password=password,
        sub_user=sub_user,
        country=country,
        region=region,
        city=city,
        sticky=sticky,
        filter=filter,
        protocol=protocol,
    )
    opts: dict[str, Any] = dict(base) if base else {}
    opts["proxy"] = url
    return opts


def _build_proxyhat_youtubedl() -> type[YoutubeDL]:
    """Define the ``ProxyHatYoutubeDL`` subclass against the installed yt-dlp.

    Built lazily (on first attribute access) so that importing this module never
    requires yt-dlp — only using the subclass does.
    """
    from yt_dlp import YoutubeDL

    class ProxyHatYoutubeDL(YoutubeDL):
        """A ``yt_dlp.YoutubeDL`` that downloads through a ProxyHat residential IP.

        Drop-in for ``yt_dlp.YoutubeDL``: it builds the gateway proxy URL from
        your ProxyHat credentials + targeting and injects it into the params
        dict's ``proxy`` key before handing off to yt-dlp. Sticky by default
        (one pinned residential IP for the whole download); pass ``sticky=False``
        for a fresh IP per run. The first positional ``params`` dict and any
        extra keyword arguments (e.g. ``auto_init``) are forwarded to
        ``yt_dlp.YoutubeDL`` unchanged.

        ```python
        from yt_dlp_proxyhat import ProxyHatYoutubeDL

        with ProxyHatYoutubeDL({"format": "best"}, country="us") as ydl:
            ydl.download(["https://www.youtube.com/watch?v=..."])
        ```

        The resolved proxy URL is available as ``ydl.proxyhat_url``.
        """

        def __init__(
            self,
            params: dict[str, Any] | None = None,
            *,
            api_key: str | None = None,
            username: str | None = None,
            password: str | None = None,
            sub_user: str | None = None,
            country: str | None = None,
            region: str | None = None,
            city: str | None = None,
            sticky: bool | str | None = DEFAULT_STICKY,
            filter: str | None = None,
            protocol: str = "http",
            **ydl_kwargs: Any,
        ) -> None:
            opts = proxyhat_ydl_opts(
                api_key=api_key,
                username=username,
                password=password,
                sub_user=sub_user,
                country=country,
                region=region,
                city=city,
                sticky=sticky,
                filter=filter,
                protocol=protocol,
                base=params,
            )
            self.proxyhat_url = opts["proxy"]
            super().__init__(opts, **ydl_kwargs)

    return ProxyHatYoutubeDL


def __getattr__(name: str) -> Any:
    # PEP 562 lazy attribute: `ProxyHatYoutubeDL` is built on first access so the
    # yt-dlp import stays off the hot path of `import yt_dlp_proxyhat`. Not cached
    # so tests that inject a fake `yt_dlp` module each get a fresh, matching class.
    if name == "ProxyHatYoutubeDL":
        return _build_proxyhat_youtubedl()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
