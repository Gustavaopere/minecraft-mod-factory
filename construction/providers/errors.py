from __future__ import annotations

ERROR_CODES = frozenset({
    "INVALID_PROVIDER_PROFILE",
    "UNKNOWN_PROVIDER",
    "PROOF_LEVEL_INSUFFICIENT",
    "INTEGRATION_MODE_NOT_ALLOWED",
    "CAPABILITY_NOT_PROVEN",
    "UNVERIFIED_API",
    "INVALID_HANDOFF_REQUEST",
    "REQUEST_PROFILE_MISMATCH",
    "INVALID_HANDOFF_RECEIPT",
    "ARTIFACT_LIMIT_EXCEEDED",
    "ARTIFACT_HASH_MISMATCH",
    "ARTIFACT_KIND_UNSUPPORTED",
    "FORMAT_VALIDATION_FAILED",
    "MANUAL_ACTION_REQUIRED",
    "PROVIDER_DRIFT_DETECTED",
    "INTERNAL_ERROR",
})


class C10Error(ValueError):
    """Stable sanitized error for the C10 external-provider boundary."""

    def __init__(self, code: str, message: str) -> None:
        if code not in ERROR_CODES:
            raise ValueError("unknown C10 error code")
        if not isinstance(message, str) or not message:
            raise ValueError("C10 error message must be non-empty")
        self.code = code
        super().__init__(message)
