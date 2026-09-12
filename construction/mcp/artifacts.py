from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Callable

from .errors import C9Error


MAX_ARTIFACT_BYTES = 64 * 1024 * 1024
MAX_TOTAL_UNIQUE_BYTES = 256 * 1024 * 1024
MAX_UNIQUE_RECORDS = 512

_ARTIFACT_URI_RE = re.compile(r"^construction://artifact/sha256/([0-9a-f]{64})$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MEDIA_TYPE_BY_KIND = {
    "preview_svg": "image/svg+xml",
    "preview_bundle": "application/json",
    "sponge_v3": "application/octet-stream",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    uri: str
    data: bytes
    media_type: str
    sha256: str
    byte_length: int
    kind: str

    def descriptor(self) -> dict[str, object]:
        return {
            "uri": self.uri,
            "media_type": self.media_type,
            "sha256": self.sha256,
            "byte_length": self.byte_length,
            "kind": self.kind,
        }


class ArtifactStore:
    """Process-scoped immutable content-addressed artifact storage."""

    def __init__(self, *, _digest_fn: Callable[[bytes], str] | None = None) -> None:
        self._digest_fn = _digest_fn or _sha256
        self._records: dict[str, ArtifactRecord] = {}
        self._total_unique_bytes = 0

    def put(self, data: bytes, *, media_type: str, kind: str) -> dict[str, object]:
        if not isinstance(data, bytes):
            raise C9Error("INVALID_INPUT", "artifact data must be bytes")
        expected_media_type = _MEDIA_TYPE_BY_KIND.get(kind)
        if expected_media_type is None:
            raise C9Error("INVALID_INPUT", "artifact kind is not supported")
        if media_type != expected_media_type:
            raise C9Error("INVALID_INPUT", "artifact media type does not match its kind")

        digest = self._digest_fn(data)
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            raise C9Error("INTERNAL_ERROR", "artifact digest generation failed")
        uri = f"construction://artifact/sha256/{digest}"

        existing = self._records.get(uri)
        if existing is not None:
            if existing.data != data:
                raise C9Error("INTERNAL_ERROR", "artifact SHA-256 collision detected")
            return existing.descriptor()

        byte_length = len(data)
        if byte_length > MAX_ARTIFACT_BYTES:
            raise C9Error("ARTIFACT_LIMIT", "artifact exceeds the per-artifact byte limit")
        if len(self._records) >= MAX_UNIQUE_RECORDS:
            raise C9Error("ARTIFACT_LIMIT", "artifact store record limit exceeded")
        if self._total_unique_bytes + byte_length > MAX_TOTAL_UNIQUE_BYTES:
            raise C9Error("ARTIFACT_LIMIT", "artifact store byte limit exceeded")

        record = ArtifactRecord(
            uri=uri,
            data=data,
            media_type=media_type,
            sha256=digest,
            byte_length=byte_length,
            kind=kind,
        )
        self._records[uri] = record
        self._total_unique_bytes += byte_length
        return record.descriptor()

    def get(self, uri: str) -> ArtifactRecord:
        if not isinstance(uri, str) or _ARTIFACT_URI_RE.fullmatch(uri) is None:
            raise C9Error("INVALID_INPUT", "artifact URI is invalid")
        record = self._records.get(uri)
        if record is None:
            raise C9Error("ARTIFACT_NOT_FOUND", "artifact URI is not present in this process")
        return record

    def list_descriptors(self) -> list[dict[str, object]]:
        return [self._records[uri].descriptor() for uri in sorted(self._records)]
