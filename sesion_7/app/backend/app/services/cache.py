"""Cache persistente de embeddings (SQLite, solo librería estándar).

Idea central: un embedding es una función *determinista* del par (modelo, texto).
Si el mismo texto se vuelve a pedir, recalcularlo desperdicia GPU/CPU y latencia.
La clave es sha256(modelo + "\\0" + texto); el valor es el vector en float32.
"""

from __future__ import annotations

import hashlib
import sqlite3
import threading
import time
from array import array
from pathlib import Path


def _key(model: str, text: str) -> str:
    return hashlib.sha256(f"{model}\0{text}".encode()).hexdigest()


class EmbeddingCache:
    def __init__(self, path: str = ":memory:", max_entries: int = 50_000) -> None:
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        self._max = max_entries
        self.hits = 0
        self.misses = 0
        with self._lock:
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS emb ("
                "k TEXT PRIMARY KEY, model TEXT NOT NULL, dim INTEGER NOT NULL, "
                "vec BLOB NOT NULL, last_used REAL NOT NULL)"
            )
            self._db.commit()

    def get_many(self, model: str, texts: list[str]) -> dict[int, list[float]]:
        """Devuelve {índice: vector} solo para los textos presentes en cache."""
        found: dict[int, list[float]] = {}
        now = time.time()
        with self._lock:
            for i, t in enumerate(texts):
                row = self._db.execute("SELECT vec FROM emb WHERE k = ?", (_key(model, t),)).fetchone()
                if row is None:
                    self.misses += 1
                    continue
                arr = array("f")
                arr.frombytes(row[0])
                found[i] = arr.tolist()
                self.hits += 1
                self._db.execute("UPDATE emb SET last_used = ? WHERE k = ?", (now, _key(model, t)))
            self._db.commit()
        return found

    def put_many(self, model: str, texts: list[str], vectors: list[list[float]]) -> None:
        now = time.time()
        with self._lock:
            for t, v in zip(texts, vectors, strict=True):
                self._db.execute(
                    "INSERT OR REPLACE INTO emb (k, model, dim, vec, last_used) VALUES (?,?,?,?,?)",
                    (_key(model, t), model, len(v), array("f", v).tobytes(), now),
                )
            self._evict_if_needed()
            self._db.commit()

    def _evict_if_needed(self) -> None:
        (count,) = self._db.execute("SELECT COUNT(*) FROM emb").fetchone()
        if count > self._max:
            drop = max(1, count - int(self._max * 0.9))
            self._db.execute(
                "DELETE FROM emb WHERE k IN (SELECT k FROM emb ORDER BY last_used ASC LIMIT ?)", (drop,)
            )

    def stats(self) -> dict[str, float | int]:
        with self._lock:
            (size,) = self._db.execute("SELECT COUNT(*) FROM emb").fetchone()
        total = self.hits + self.misses
        return {
            "entries": size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": (self.hits / total) if total else 0.0,
        }

    def clear(self) -> None:
        with self._lock:
            self._db.execute("DELETE FROM emb")
            self._db.commit()
            self.hits = 0
            self.misses = 0

    def close(self) -> None:
        with self._lock:
            self._db.close()
