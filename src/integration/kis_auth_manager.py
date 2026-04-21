"""KIS access token manager with local cache-first policy."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib import error, request


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _safe_error_summary(body_text: str) -> str:
    """Extract only non-sensitive error fields."""
    try:
        data = json.loads(body_text) if body_text else {}
    except json.JSONDecodeError:
        return "unknown_error"
    msg_cd = str(data.get("msg_cd") or data.get("error_code") or "").strip()
    msg1 = str(data.get("msg1") or data.get("error_description") or "").strip()
    if msg_cd and msg1:
        return f"{msg_cd}: {msg1}"
    if msg_cd:
        return msg_cd
    if msg1:
        return msg1
    return "unknown_error"


@dataclass
class TokenState:
    access_token: str
    issued_at: datetime
    expires_at: datetime
    environment: str


class KISAuthManager:
    """Single-responsibility manager for KIS token issue/cache/reuse."""

    def __init__(
        self,
        *,
        app_key: str,
        app_secret: str,
        environment: str,
        base_url: str,
        cache_path: str | None = None,
        expiry_margin_seconds: int = 300,
    ) -> None:
        self.app_key = app_key
        self.app_secret = app_secret
        self.environment = environment.strip().lower()
        self.base_url = base_url.rstrip("/")
        self.expiry_margin_seconds = expiry_margin_seconds
        resolved_cache = cache_path or os.environ.get("KIS_TOKEN_CACHE_PATH", ".kis_token_cache.json")
        self.cache_path = Path(resolved_cache)
        self._in_memory_state: TokenState | None = None

    def get_valid_access_token(self) -> str:
        force_refresh = os.environ.get("KIS_TOKEN_FORCE_REFRESH", "").strip().lower() in ("1", "true", "yes")
        return self._get_valid_access_token(force_refresh=force_refresh)

    def force_refresh_access_token(self) -> str:
        return self._get_valid_access_token(force_refresh=True)

    def _get_valid_access_token(self, *, force_refresh: bool) -> str:
        cached = self._load_cached_state()
        if not force_refresh and cached is not None and self._is_state_valid(cached):
            self._in_memory_state = cached
            return cached.access_token

        try:
            issued = self._issue_new_access_token()
            self._persist_state(issued)
            self._in_memory_state = issued
            return issued.access_token
        except RuntimeError as exc:
            # If issuance is rate-limited but existing token is still valid, keep running with cache.
            if cached is not None and self._is_state_valid(cached) and "EGW00133" in str(exc):
                self._in_memory_state = cached
                return cached.access_token
            raise

    def describe_token_state(self) -> dict[str, str | bool]:
        state = self._load_cached_state()
        env_match = state is not None and state.environment == self.environment
        expired = True if state is None else not self._is_state_valid(state)
        return {
            "cache_exists": self.cache_path.exists(),
            "token_present": state is not None and bool(state.access_token),
            "environment_match": env_match,
            "expired": expired,
        }

    def _is_state_valid(self, state: TokenState) -> bool:
        if state.environment != self.environment:
            return False
        now = _utc_now()
        return now + timedelta(seconds=self.expiry_margin_seconds) < state.expires_at

    def _load_cached_state(self) -> TokenState | None:
        if self._in_memory_state is not None:
            return self._in_memory_state
        if not self.cache_path.exists():
            return None
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        token = str(payload.get("access_token", "")).strip()
        issued_at = _parse_time(payload.get("issued_at"))
        expires_at = _parse_time(payload.get("expires_at"))
        env = str(payload.get("environment", "")).strip().lower()
        if not token or issued_at is None or expires_at is None or not env:
            return None
        return TokenState(access_token=token, issued_at=issued_at, expires_at=expires_at, environment=env)

    def _persist_state(self, state: TokenState) -> None:
        payload = {
            "access_token": state.access_token,
            "issued_at": state.issued_at.isoformat(),
            "expires_at": state.expires_at.isoformat(),
            "environment": state.environment,
        }
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(payload), encoding="utf-8")

    def _issue_new_access_token(self) -> TokenState:
        token_url = f"{self.base_url}/oauth2/tokenP"
        req = request.Request(
            token_url,
            data=json.dumps(
                {
                    "grant_type": "client_credentials",
                    "appkey": self.app_key,
                    "appsecret": self.app_secret,
                }
            ).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        try:
            with request.urlopen(req, timeout=15) as response:
                body_text = response.read().decode("utf-8")
        except error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="ignore") if exc.fp is not None else ""
            summary = _safe_error_summary(body_text)
            raise RuntimeError(f"KIS token issue failed ({exc.code}): {summary}") from exc

        data = json.loads(body_text) if body_text else {}
        token = str(data.get("access_token", "")).strip()
        if not token:
            raise RuntimeError(f"KIS token issue failed: {_safe_error_summary(body_text)}")
        now = _utc_now()
        expires_in_raw = data.get("expires_in")
        expires_in = int(expires_in_raw) if isinstance(expires_in_raw, (int, str)) and str(expires_in_raw).isdigit() else 3600
        return TokenState(
            access_token=token,
            issued_at=now,
            expires_at=now + timedelta(seconds=max(expires_in, 1)),
            environment=self.environment,
        )

