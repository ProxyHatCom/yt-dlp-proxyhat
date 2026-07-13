"""Shared test doubles — a fake ProxyHat SDK whose ``sub_users.list()`` is stubbed."""

from __future__ import annotations

from types import SimpleNamespace


def sub_user(**kw):
    """Build a fake sub-user object shaped like the SDK's."""
    base = dict(
        uuid="u",
        name=None,
        proxy_username="ph-1",
        proxy_password="pw",
        traffic_limit=0,
        used_traffic=0,
        suspended_at=None,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def patch_sdk(monkeypatch, users):
    """Make ``proxyhat.ProxyHat(...).sub_users.list()`` return ``users`` — no network."""
    fake_client = SimpleNamespace(sub_users=SimpleNamespace(list=lambda: users))
    monkeypatch.setattr("yt_dlp_proxyhat._resolve.ProxyHat", lambda **kw: fake_client)
    return fake_client
