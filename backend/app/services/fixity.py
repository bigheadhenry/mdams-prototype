from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO


CHUNK_SIZE = 1024 * 1024


def calculate_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        _update_digest(stream, digest)
    return digest.hexdigest()


def _update_digest(stream: BinaryIO, digest) -> None:
    while chunk := stream.read(CHUNK_SIZE):
        digest.update(chunk)


@dataclass(frozen=True)
class FixityResult:
    expected_sha256: str | None
    actual_sha256: str | None
    status: str
    verified_at: datetime
    message: str


def verify_path(path: str | Path, expected_sha256: str | None) -> FixityResult:
    verified_at = datetime.now(timezone.utc)
    candidate = Path(path)
    if not candidate.exists() or not candidate.is_file():
        return FixityResult(expected_sha256, None, "missing", verified_at, "File is missing")
    actual = calculate_sha256(candidate)
    if not expected_sha256:
        return FixityResult(actual, actual, "recorded", verified_at, "Baseline checksum recorded")
    if actual == expected_sha256:
        return FixityResult(expected_sha256, actual, "verified", verified_at, "Checksum verified")
    return FixityResult(expected_sha256, actual, "mismatch", verified_at, "Checksum mismatch")
