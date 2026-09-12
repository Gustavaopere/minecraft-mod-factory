from __future__ import annotations

from typing import Any


ERROR_CODES = frozenset({
    "INVALID_INPUT",
    "AUTHORITY_REJECTED",
    "ARTIFACT_NOT_FOUND",
    "ARTIFACT_LIMIT",
    "INTERNAL_ERROR",
})
AUTHORITIES = frozenset({"C2", "C4", "C5", "C6", "C7", "C8"})


def _safe_details(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, (list, tuple)):
        return [_safe_details(item) for item in value]
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("C9 error details object keys must be strings")
        return {key: _safe_details(value[key]) for key in sorted(value)}
    raise ValueError("C9 error details must contain deterministic JSON-safe values")


class C9Error(ValueError):
    """Stable, sanitized error surfaced by the C9 boundary."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        authority: str | None = None,
        details: Any = None,
    ) -> None:
        if code not in ERROR_CODES:
            raise ValueError("unsupported C9 error code")
        if not isinstance(message, str) or not message:
            raise ValueError("C9 error message must be a non-empty string")
        if code == "AUTHORITY_REJECTED":
            if authority not in AUTHORITIES:
                raise ValueError("AUTHORITY_REJECTED requires a C2-C8 authority")
        elif authority is not None:
            raise ValueError("authority is valid only for AUTHORITY_REJECTED")

        self.code = code
        self.message = message
        self.authority = authority
        self.details = _safe_details(details) if details is not None else None
        super().__init__(message)

    def payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.authority is not None:
            payload["authority"] = self.authority
        if self.details is not None:
            payload["details"] = _safe_details(self.details)
        return payload
