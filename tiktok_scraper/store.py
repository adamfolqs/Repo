"""Append-only JSONL stores, so a long run survives being interrupted.

Discovery and enrichment over a few thousand videos takes hours at a polite
request rate. Holding all of that in memory until the end means a crash, a
rate-limit, or a closed laptop loses the entire haul. Instead every resolved
record is appended to disk immediately, and each stage skips the ids already
present -- so re-running a stage resumes rather than restarts, and never
re-requests something TikTok already answered.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator

from pydantic import BaseModel


def append(path: str | Path, records: Iterable[BaseModel]) -> int:
    """Append pydantic records as one JSON object per line."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with target.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(record.model_dump_json() + "\n")
            count += 1
    return count


def read(path: str | Path) -> Iterator[dict]:
    """Every record in a store, skipping any line torn by an interrupted write."""
    target = Path(path)
    if not target.exists():
        return
    with target.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue  # a half-written final line from a killed process


def done_keys(path: str | Path, key: str) -> set[str]:
    """The set of `key` values already stored — what a resumed run can skip."""
    return {str(record[key]) for record in read(path) if record.get(key)}
