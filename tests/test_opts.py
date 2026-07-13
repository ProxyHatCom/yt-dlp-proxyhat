"""``proxyhat_ydl_opts`` and ``ProxyHatYoutubeDL`` — the yt-dlp wiring.

yt-dlp is a heavy optional dependency, so instead of installing it we inject a
tiny fake ``yt_dlp`` module whose ``YoutubeDL`` records the params it receives.
That verifies our wiring — proxy URL injected into the opts dict, base opts and
extra kwargs forwarded — without any yt-dlp install or network.
"""

import sys
from types import ModuleType, SimpleNamespace

import pytest

from yt_dlp_proxyhat import proxyhat_ydl_opts


class TestYdlOpts:
    def test_injects_proxy_key(self):
        opts = proxyhat_ydl_opts(username="ph-1", password="pw", country="us")
        assert opts["proxy"].startswith("http://ph-1-country-us")
        assert "@gate.proxyhat.com:8080" in opts["proxy"]

    def test_sticky_default_pins_one_ip(self):
        opts = proxyhat_ydl_opts(username="ph-1", password="pw")
        assert "-sid-" in opts["proxy"]
        assert "-ttl-30m" in opts["proxy"]

    def test_rotating_per_run(self):
        opts = proxyhat_ydl_opts(username="ph-1", password="pw", sticky=False)
        assert "-sid-" not in opts["proxy"]

    def test_socks5(self):
        opts = proxyhat_ydl_opts(username="ph-1", password="pw", protocol="socks5", sticky=False)
        assert opts["proxy"].startswith("socks5://")

    def test_base_opts_pass_through(self):
        base = {"format": "bestvideo+bestaudio", "geo_bypass": True}
        opts = proxyhat_ydl_opts(username="ph-1", password="pw", country="us", base=base)
        assert opts["format"] == "bestvideo+bestaudio"
        assert opts["geo_bypass"] is True
        assert "proxy" in opts
        # base is copied, not mutated.
        assert "proxy" not in base

    def test_our_proxy_wins_over_base_proxy(self):
        opts = proxyhat_ydl_opts(username="ph-1", password="pw", country="us", base={"proxy": "http://old:1"})
        assert "gate.proxyhat.com" in opts["proxy"]


@pytest.fixture
def fake_yt_dlp(monkeypatch):
    captured = {}

    class YoutubeDL:
        def __init__(self, params=None, **kwargs):
            captured["params"] = params
            captured["kwargs"] = kwargs
            self.params = params

    module = ModuleType("yt_dlp")
    module.YoutubeDL = YoutubeDL
    monkeypatch.setitem(sys.modules, "yt_dlp", module)
    return SimpleNamespace(captured=captured, cls=YoutubeDL)


class TestProxyHatYoutubeDL:
    def test_injects_proxy_and_forwards_base_and_kwargs(self, fake_yt_dlp):
        from yt_dlp_proxyhat import ProxyHatYoutubeDL

        ydl = ProxyHatYoutubeDL(
            {"format": "best"},
            username="ph-1",
            password="pw",
            country="us",
            auto_init=False,
        )
        assert isinstance(ydl, fake_yt_dlp.cls)
        params = fake_yt_dlp.captured["params"]
        # Base opt preserved, proxy injected, sticky-by-default one IP.
        assert params["format"] == "best"
        assert params["proxy"].startswith("http://ph-1-country-us")
        assert "-sid-" in params["proxy"]
        # Resolved URL exposed on the instance.
        assert ydl.proxyhat_url == params["proxy"]
        # Extra yt-dlp kwargs forwarded untouched.
        assert fake_yt_dlp.captured["kwargs"] == {"auto_init": False}

    def test_rotating_option(self, fake_yt_dlp):
        from yt_dlp_proxyhat import ProxyHatYoutubeDL

        ydl = ProxyHatYoutubeDL(username="ph-1", password="pw", sticky=False)
        assert "-sid-" not in ydl.params["proxy"]

    def test_defaults_params_to_just_proxy(self, fake_yt_dlp):
        from yt_dlp_proxyhat import ProxyHatYoutubeDL

        ydl = ProxyHatYoutubeDL(username="ph-1", password="pw", country="de", sticky=False)
        assert ydl.params == {"proxy": "http://ph-1-country-de:pw@gate.proxyhat.com:8080"}
