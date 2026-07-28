"""

Local cache layer using SQLite + orjson for fast serialization.

Caches video metadata, search results, and transcripts with TTL expiry.

"""

from __future__ import annotations



import hashlib

import sqlite3

import time

from pathlib import Path

from typing import Any



import orjson



DEFAULT_CACHE_DIR = Path.home() / ".cache" / "youtube-ai"

DEFAULT_TTL = 3600





class Cache:

    """SQLite-backed cache with orjson serialization."""



    def __init__(self, cache_dir: Path | str | None = None, ttl: int = DEFAULT_TTL):

        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.cache_dir / "cache.db"

        self.ttl = ttl

        self._init_db()



    def _init_db(self):

        with sqlite3.connect(str(self.db_path)) as conn:

            conn.execute("""

                CREATE TABLE IF NOT EXISTS cache (

                    key TEXT PRIMARY KEY,

                    value BLOB NOT NULL,

                    created_at REAL NOT NULL,

                    ttl INTEGER NOT NULL

                )

            """)

            conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON cache(created_at)")



    def _make_key(self, namespace: str, identifier: str) -> str:

        raw = f"{namespace}:{identifier}"

        return hashlib.sha256(raw.encode()).hexdigest()



    def get(self, namespace: str, identifier: str) -> Any | None:

        key = self._make_key(namespace, identifier)

        with sqlite3.connect(str(self.db_path)) as conn:

            row = conn.execute(

                "SELECT value, created_at, ttl FROM cache WHERE key = ?", (key,)

            ).fetchone()

        if row is None:

            return None

        value_blob, created_at, ttl = row

        if time.time() - created_at > ttl:

            return None

        return orjson.loads(value_blob)



    def set(self, namespace: str, identifier: str, value: Any, ttl: int | None = None):

        key = self._make_key(namespace, identifier)

        blob = orjson.dumps(value)

        effective_ttl = ttl if ttl is not None else self.ttl

        with sqlite3.connect(str(self.db_path)) as conn:

            conn.execute(

                "INSERT OR REPLACE INTO cache (key, value, created_at, ttl) VALUES (?, ?, ?, ?)",

                (key, blob, time.time(), effective_ttl),

            )



    def delete(self, namespace: str, identifier: str):

        key = self._make_key(namespace, identifier)

        with sqlite3.connect(str(self.db_path)) as conn:

            conn.execute("DELETE FROM cache WHERE key = ?", (key,))



    def clear(self):

        with sqlite3.connect(str(self.db_path)) as conn:

            conn.execute("DELETE FROM cache")



    def cleanup_expired(self):

        now = time.time()

        with sqlite3.connect(str(self.db_path)) as conn:

            conn.execute(

                "DELETE FROM cache WHERE ? - created_at > ttl", (now,)

            )



    def stats(self) -> dict:

        with sqlite3.connect(str(self.db_path)) as conn:

            total = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]

            expired = conn.execute(

                "SELECT COUNT(*) FROM cache WHERE ? - created_at > ttl", (time.time(),)

            ).fetchone()[0]

        return {"total_entries": total, "expired_entries": expired, "active": total - expired}



    def close(self):

        """No-op — SQLite connections are opened per-operation, no persistent connection to close."""

        pass
