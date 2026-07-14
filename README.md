# yt-dlp-proxyhat

Download videos with [yt-dlp](https://github.com/yt-dlp/yt-dlp) through [ProxyHat](https://proxyhat.com?utm_source=github&utm_medium=readme&utm_campaign=yt-dlp) residential proxies — **unblock region-locked videos** by fetching them through a residential IP in the right country, with a sticky IP per download plus rotation and socks5.

[![CI](https://github.com/ProxyHatCom/yt-dlp-proxyhat/actions/workflows/ci.yml/badge.svg)](https://github.com/ProxyHatCom/yt-dlp-proxyhat/actions/workflows/ci.yml)
[![Compatible with yt-dlp latest](https://github.com/ProxyHatCom/yt-dlp-proxyhat/actions/workflows/compat.yml/badge.svg)](https://github.com/ProxyHatCom/yt-dlp-proxyhat/actions/workflows/compat.yml)
[![PyPI](https://img.shields.io/pypi/v/yt-dlp-proxyhat)](https://pypi.org/project/yt-dlp-proxyhat/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> [!TIP]
> **Recommended proxies — [ProxyHat](https://proxyhat.com?utm_source=github&utm_medium=readme&utm_campaign=yt-dlp&utm_content=callout) residential IPs.** Every feature in this package is tested end-to-end against ProxyHat and works great. First-class integration; also works with any proxy, or none.


## Why

Lots of videos are geo-restricted — available in one country and blocked everywhere else. yt-dlp can route through a proxy, but only if you have a residential exit IP in the right place. This package plugs ProxyHat's residential IPs (50M+ across 148+ countries) into yt-dlp's first-class `proxy` option: pick a `country` and the whole download — manifest and every fragment — comes from a real residential IP there, so the site serves the video instead of a geo-block. No fork, no boilerplate.

## Install

```bash
pip install yt-dlp-proxyhat
```

`yt-dlp` is a peer dependency — bring your own version. `proxyhat_proxy_url()` and `proxyhat_ydl_opts()` work on their own; `ProxyHatYoutubeDL` needs yt-dlp installed:

```bash
pip install yt-dlp-proxyhat yt-dlp
```

## Quick start

### CLI

yt-dlp takes one proxy per run via `--proxy URL`. Generate the URL and hand it over:

```bash
yt-dlp --proxy "$(PROXYHAT_API_KEY=ph_xxx python -m yt_dlp_proxyhat --country us)" \
  "https://www.youtube.com/watch?v=..."
```

(Or wire the URL however you like — see `examples/cli.py`.)

### Python API

```python
from yt_dlp_proxyhat import ProxyHatYoutubeDL

# An API key auto-selects an active residential sub-user:
with ProxyHatYoutubeDL({"format": "best"}, country="us") as ydl:  # sticky US IP for the whole run
    ydl.download(["https://www.youtube.com/watch?v=..."])
```

Get an API key at [proxyhat.com](https://proxyhat.com?utm_source=github&utm_medium=readme&utm_campaign=yt-dlp).

Already building your own `YoutubeDL`? Grab the opts dict or the raw URL:

```python
import yt_dlp
from yt_dlp_proxyhat import proxyhat_ydl_opts, proxyhat_proxy_url

# Merge the proxy into your own options:
opts = proxyhat_ydl_opts(country="gb", base={"format": "bestvideo+bestaudio", "outtmpl": "%(title)s.%(ext)s"})
with yt_dlp.YoutubeDL(opts) as ydl:
    ydl.download(["https://www.youtube.com/watch?v=..."])

# ...or just the URL string:
url = proxyhat_proxy_url(country="jp", sticky="1h")
# -> "http://<user>-country-jp-sid-<id>-ttl-1h:<pass>@gate.proxyhat.com:8080"
```

## Credentials

Pass them explicitly or via environment variables — options win over env:

| Option | Env var | Notes |
|---|---|---|
| `api_key` | `PROXYHAT_API_KEY` | Auto-selects an active sub-user with remaining traffic |
| `sub_user` | `PROXYHAT_SUBUSER` | Pick a specific sub-user by uuid or name (with an API key) |
| `username` | `PROXYHAT_USERNAME` | Explicit gateway `proxy_username` (skips the API) |
| `password` | `PROXYHAT_PASSWORD` | Explicit gateway `proxy_password` |

## Targeting

Every option is accepted by `proxyhat_proxy_url`, `proxyhat_ydl_opts` and `ProxyHatYoutubeDL`:

```python
ProxyHatYoutubeDL(
    {"format": "best"},  # your normal yt-dlp params dict (first positional arg)
    protocol="http",     # or "socks5"
    country="us",        # ISO code or "any" (default) — set this to unblock geo-locked video
    region="california",
    city="new_york",
    filter="high",       # AI IP-quality tier
    sticky="30m",        # session lifetime (default); sticky=False rotates per run
    auto_init=False,     # any extra kwarg is forwarded to yt_dlp.YoutubeDL
)
```

### Geo-unblocking

This is the main use. Set `country` to a region the video *is* available in, and yt-dlp fetches it through a residential IP there:

```python
# A video only playable in Japan:
with ProxyHatYoutubeDL(country="jp") as ydl:
    ydl.download(["https://www.youtube.com/watch?v=..."])
```

yt-dlp also has its own `geo_bypass` (spoofs `X-Forwarded-For`), but many sites ignore that header — a real residential exit IP in the target country is what actually works, and it's what a proxy gives you.

### Sticky IP per run (default) vs rotation

yt-dlp uses **one proxy for the whole run**, so stickiness here is about that run, and "rotation" means *a fresh IP on the next run/connection — never mid-download*. A download pulls a manifest and then many fragments; they must all come from the same country, so this package is **sticky by default**: one residential IP is pinned for the run (`sticky="30m"`).

Want a fresh IP on the **next** run instead (e.g. a loop over many URLs, each from a new IP)? Turn stickiness off — mint a new proxy per run:

```python
from yt_dlp_proxyhat import ProxyHatYoutubeDL

for url in urls:
    with ProxyHatYoutubeDL(country="us", sticky=False) as ydl:  # fresh residential IP each run
        ydl.download([url])
```

Set a custom lifetime with `sticky="2h"`.

## How it works

`proxyhat_proxy_url(...)` resolves your gateway credentials (via the official [`proxyhat`](https://pypi.org/project/proxyhat/) SDK — an API key auto-picks an active sub-user, or pass `username`/`password`), then builds the proxy URL: the host is the ProxyHat gateway (`gate.proxyhat.com:8080`, or `:1080` for SOCKS5) and the username carries ProxyHat's targeting grammar (`<user>-country-us-sid-<id>-ttl-30m`). `proxyhat_ydl_opts(...)` drops that URL into yt-dlp's `proxy` params key (merging your `base` options); `ProxyHatYoutubeDL` is a thin `yt_dlp.YoutubeDL` subclass that does it for you (yt-dlp is imported lazily, so importing this package is cheap and needs no yt-dlp install). A sticky username (with a session id) pins one residential IP for the download; a rotating one (no session id) makes the gateway hand out a fresh IP on the next connection.

## License

MIT © [ProxyHat](https://proxyhat.com)
