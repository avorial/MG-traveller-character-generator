"""
Unique-visitor counter for the terminal-id badge.

Counts distinct client IPs that have loaded the page. IPs are never stored in
the clear — each is salted and SHA-256 hashed, so the on-disk file holds only
opaque hashes plus a random salt. The count is simply the number of distinct
hashes seen. Persisted to a JSON file (put it on a Docker volume so the count
survives container rebuilds).
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from pathlib import Path


class VisitorCounter:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()
        self._hashes: set[str] = set()
        self._salt = ""
        self._load()

    def _load(self) -> None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self._salt = data.get("salt") or ""
            self._hashes = set(data.get("hashes") or [])
        except (FileNotFoundError, ValueError, OSError):
            self._salt, self._hashes = "", set()
        if not self._salt:
            self._salt = hashlib.sha256(os.urandom(16)).hexdigest()[:16]

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(
                json.dumps({"salt": self._salt, "hashes": sorted(self._hashes)}),
                encoding="utf-8",
            )
            tmp.replace(self.path)
        except OSError:
            pass  # counting is best-effort; never break a page load over it

    def record(self, ip: str | None) -> int:
        """Record a visit from `ip` and return the current distinct-IP count."""
        if not ip:
            return len(self._hashes)
        h = hashlib.sha256(f"{self._salt}:{ip}".encode("utf-8")).hexdigest()
        with self._lock:
            if h not in self._hashes:
                self._hashes.add(h)
                self._save()
            return len(self._hashes)

    @property
    def count(self) -> int:
        return len(self._hashes)
