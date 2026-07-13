"""``proxyhat_proxy_url`` builds the gateway proxy URL — pure, offline, no yt-dlp."""

from conftest import patch_sdk, sub_user

from yt_dlp_proxyhat import proxyhat_proxy_url


class TestProxyUrl:
    def test_geo_reflected_in_url(self):
        # Geo-unblocking: country pins the exit-IP region into the username.
        url = proxyhat_proxy_url(username="ph-1", password="pw", country="us", sticky=False)
        assert url == "http://ph-1-country-us:pw@gate.proxyhat.com:8080"

    def test_sticky_default_pins_one_ip_for_the_download(self):
        url = proxyhat_proxy_url(username="ph-1", password="pw")
        # Default is sticky: a session id + 30m TTL so the whole run uses one IP.
        assert "-sid-" in url
        assert "-ttl-30m" in url

    def test_sticky_false_rotates_per_run(self):
        url = proxyhat_proxy_url(username="ph-1", password="pw", sticky=False)
        assert "-sid-" not in url
        assert "-ttl-" not in url

    def test_custom_sticky_ttl(self):
        url = proxyhat_proxy_url(username="ph-1", password="pw", sticky="2h")
        assert "-sid-" in url
        assert "-ttl-2h" in url

    def test_full_geo_targeting(self):
        url = proxyhat_proxy_url(
            username="ph-1",
            password="pw",
            country="jp",
            region="tokyo",
            city="tokyo",
            filter="high",
            sticky=False,
        )
        assert "ph-1-country-jp" in url
        assert "-region-tokyo" in url
        assert "-city-tokyo" in url
        assert "-filter-high" in url

    def test_http_port_and_scheme(self):
        url = proxyhat_proxy_url(username="ph-1", password="pw", sticky=False)
        assert url.startswith("http://")
        assert "@gate.proxyhat.com:8080" in url

    def test_socks5_protocol(self):
        url = proxyhat_proxy_url(username="ph-1", password="pw", protocol="socks5", sticky=False)
        assert url.startswith("socks5://")
        assert "@gate.proxyhat.com:1080" in url

    def test_credentials_are_url_encoded(self):
        # A password with URL-unsafe characters must be percent-encoded so yt-dlp parses it.
        url = proxyhat_proxy_url(username="ph-1", password="p@ss:word", sticky=False)
        assert "p%40ss%3Aword" in url


class TestProxyUrlViaApiKey:
    def test_resolves_via_api_key(self, monkeypatch):
        patch_sdk(monkeypatch, [sub_user(proxy_username="good", proxy_password="secret")])
        url = proxyhat_proxy_url(api_key="ph_key", country="gb", sticky=False)
        assert url == "http://good-country-gb:secret@gate.proxyhat.com:8080"
