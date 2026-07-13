"""Print a ProxyHat proxy URL for yt-dlp's ``--proxy`` flag.

    yt-dlp --proxy "$(python -m yt_dlp_proxyhat --country jp)" URL

Credentials come from the environment (``PROXYHAT_API_KEY``, or
``PROXYHAT_USERNAME`` / ``PROXYHAT_PASSWORD``); everything yt-dlp then downloads
exits from a residential IP in the chosen country, pinned for the run.
"""

from __future__ import annotations

import argparse

from yt_dlp_proxyhat.proxy import proxyhat_proxy_url


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m yt_dlp_proxyhat",
        description="Print a ProxyHat proxy URL for `yt-dlp --proxy`.",
    )
    parser.add_argument("--country", help="ISO country code to exit from, e.g. us, gb, jp")
    parser.add_argument("--region", help="Region/state to narrow the exit IP")
    parser.add_argument("--city", help="City to narrow the exit IP")
    parser.add_argument("--filter", help="AI IP-quality tier, e.g. high")
    parser.add_argument("--protocol", default="http", choices=["http", "socks5"])
    parser.add_argument("--rotate", action="store_true", help="Fresh IP per run instead of sticky")
    args = parser.parse_args()

    print(
        proxyhat_proxy_url(
            country=args.country,
            region=args.region,
            city=args.city,
            filter=args.filter,
            protocol=args.protocol,
            sticky=False if args.rotate else "30m",
        )
    )


if __name__ == "__main__":
    main()
