"""Credential resolution — options over env, API-key sub-user auto-selection. Offline."""

import pytest
from conftest import patch_sdk, sub_user

from yt_dlp_proxyhat import ProxyHatConfigError, resolve_credentials


class TestExplicitCredentials:
    def test_username_password_wins(self, monkeypatch):
        monkeypatch.delenv("PROXYHAT_API_KEY", raising=False)
        assert resolve_credentials(username="u", password="p") == ("u", "p")

    def test_reads_env(self, monkeypatch):
        monkeypatch.setenv("PROXYHAT_USERNAME", "envu")
        monkeypatch.setenv("PROXYHAT_PASSWORD", "envp")
        assert resolve_credentials() == ("envu", "envp")

    def test_options_win_over_env(self, monkeypatch):
        monkeypatch.setenv("PROXYHAT_USERNAME", "envu")
        monkeypatch.setenv("PROXYHAT_PASSWORD", "envp")
        assert resolve_credentials(username="optu", password="optp") == ("optu", "optp")

    def test_raises_without_anything(self, monkeypatch):
        for var in ("PROXYHAT_API_KEY", "PROXYHAT_USERNAME", "PROXYHAT_PASSWORD", "PROXYHAT_SUBUSER"):
            monkeypatch.delenv(var, raising=False)
        with pytest.raises(ProxyHatConfigError):
            resolve_credentials()


class TestApiKeyResolution:
    def test_picks_first_active_sub_user(self, monkeypatch):
        patch_sdk(
            monkeypatch,
            [
                sub_user(uuid="s", proxy_username="susp", suspended_at="2026-01-01"),
                sub_user(uuid="x", proxy_username="x", traffic_limit=100, used_traffic=100),
                sub_user(uuid="ok", proxy_username="ok", traffic_limit=100, used_traffic=1),
            ],
        )
        assert resolve_credentials(api_key="ph_key") == ("ok", "pw")

    def test_selects_named_sub_user(self, monkeypatch):
        patch_sdk(
            monkeypatch,
            [sub_user(uuid="a", proxy_username="aaa"), sub_user(uuid="b", name="beta", proxy_username="bbb")],
        )
        assert resolve_credentials(api_key="ph_key", sub_user="beta") == ("bbb", "pw")

    def test_env_api_key_is_read(self, monkeypatch):
        for var in ("PROXYHAT_USERNAME", "PROXYHAT_PASSWORD", "PROXYHAT_SUBUSER"):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("PROXYHAT_API_KEY", "ph_key")
        patch_sdk(monkeypatch, [sub_user(proxy_username="good", proxy_password="secret")])
        assert resolve_credentials() == ("good", "secret")

    def test_raises_when_none_usable(self, monkeypatch):
        patch_sdk(monkeypatch, [sub_user(traffic_limit=100, used_traffic=100)])
        with pytest.raises(ProxyHatConfigError):
            resolve_credentials(api_key="ph_key")
