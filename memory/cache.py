"""
cache.py — in-memory tool result cache for a single session.

Prevents re-fetching identical URLs or re-running identical searches
within the same session. Resets when the process exits — no cross-session
persistence (brand_memory.py handles that).

Primary use case: web_fetch on brand URLs. Lila may reference the brand
site multiple times during a session (directions → image prompts). The
content won't change; re-fetching wastes tokens and time.

Usage:
    from memory.cache import session_cache

    result = session_cache.get("web_fetch", url="https://emberoak.com")
    if result is None:
        result = actual_fetch("https://emberoak.com")
        session_cache.set(result, "web_fetch", url="https://emberoak.com")
"""

import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Any


class SessionCache:
    def __init__(self, default_ttl_seconds: int = 3600):
        """
        Args:
            default_ttl_seconds: How long entries live. Default 1 hour —
                               long enough for any session, short enough
                               to avoid serving genuinely stale content.
        """
        self._store: dict[str, dict] = {}
        self._default_ttl = timedelta(seconds=default_ttl_seconds)

    def _make_key(self, tool: str, **kwargs) -> str:
        payload = json.dumps({"tool": tool, **kwargs}, sort_keys=True)
        return hashlib.md5(payload.encode()).hexdigest()

    def get(self, tool: str, **kwargs) -> Any | None:
        """
        Return cached result for this tool + args combination, or None if
        not cached / expired.
        """
        key = self._make_key(tool, **kwargs)
        entry = self._store.get(key)
        if entry is None:
            return None
        if datetime.now(timezone.utc) - entry["cached_at"] > self._default_ttl:
            del self._store[key]
            return None
        return entry["result"]

    def set(self, result: Any, tool: str, **kwargs) -> None:
        """Store a result. Overwrites any existing entry for this key."""
        key = self._make_key(tool, **kwargs)
        self._store[key] = {
            "result": result,
            "cached_at": datetime.now(timezone.utc),
            "tool": tool,
            "args": kwargs,
        }

    def invalidate(self, tool: str, **kwargs) -> None:
        """Remove a specific entry (e.g. if you know content has changed)."""
        key = self._make_key(tool, **kwargs)
        self._store.pop(key, None)

    def clear(self) -> None:
        """Wipe the entire cache. Called between sessions if reusing the process."""
        self._store.clear()

    @property
    def size(self) -> int:
        return len(self._store)

    def stats(self) -> dict:
        return {
            "entries": self.size,
            "tools": list({e["tool"] for e in self._store.values()}),
        }


# Module-level singleton — import this everywhere
session_cache = SessionCache()
