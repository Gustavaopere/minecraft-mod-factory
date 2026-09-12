from __future__ import annotations

import copy
import json
import re
from pathlib import Path

from construction.providers.common import (
    API_AUTH,
    API_CONTRACT_KINDS,
    API_STATES,
    ARTIFACT_KINDS,
    CAPABILITIES,
    DETERMINISM,
    EVIDENCE_KINDS,
    INTEGRATION_MODES,
    PROOF_LEVELS,
    PROVIDER_ID_RE,
    SHA256_RE,
    SOURCE_REF_RE,
    canonical_json_bytes,
    is_positive_int,
    is_sorted_unique_strings,
    sha256_hex,
)

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:T[^\s]+)?$")
_PROFILE_FIELDS = {
    "schema_version",
    "provider_id",
    "display_name",
    "integration_policy",
    "proof_level",
    "integration_mode",
    "capabilities",
    "audit",
    "api",
    "handoff",
    "limits",
    "profile_sha256",
}
_EVIDENCE_FIELDS = {"kind", "locator", "observed_at", "supports", "sha256"}
_API_FIELDS = {"state", "auth", "official_contract"}
_CONTRACT_FIELDS = {"kind", "locator", "version", "origin", "protocol"}
_HANDOFF_FIELDS = {
    "accepted_input_kinds",
    "output_artifact_kinds",
    "manual_action_required",
    "determinism",
}
_LIMIT_FIELDS = {"max_input_bytes", "max_output_bytes", "timeout_seconds"}
_AUDIT_FIELDS = {"audited_at", "evidence"}


def profile_fingerprint(profile: dict[str, object]) -> str:
    payload = copy.deepcopy(profile)
    payload.pop("profile_sha256", None)
    return sha256_hex(canonical_json_bytes(payload))


def _field_error(errors: list[str], label: str, value: object, expected: set[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
    elif set(value) != expected:
        errors.append(f"{label} fields do not match the C10 contract")


def _valid_locator(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if value.startswith("https://"):
        return True
    if SOURCE_REF_RE.fullmatch(value):
        return True
    if value.startswith("repo://construction/"):
        suffix = value[len("repo://construction/"):]
        return bool(suffix) and ".." not in suffix.split("/") and "\\" not in suffix
    return False


def _upstream_external_providers(upstream_registry: object) -> dict[str, dict[str, object]]:
    if not isinstance(upstream_registry, dict):
        return {}
    providers = upstream_registry.get("external_providers")
    if not isinstance(providers, list):
        return {}
    result: dict[str, dict[str, object]] = {}
    for provider in providers:
        if not isinstance(provider, dict):
            continue
        provider_id = provider.get("id")
        if isinstance(provider_id, str) and provider_id:
            result[provider_id] = provider
    return result


def validate_profile(profile: object, upstream_registry: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(profile, dict):
        return ["profile must be an object"]
    if set(profile) != _PROFILE_FIELDS:
        errors.append("profile top-level fields do not match the C10 contract")

    if profile.get("schema_version") != 1:
        errors.append("profile schema_version must be 1")

    provider_id = profile.get("provider_id")
    if not isinstance(provider_id, str) or PROVIDER_ID_RE.fullmatch(provider_id) is None:
        errors.append("provider_id must be a lowercase stable identifier")

    display_name = profile.get("display_name")
    if not isinstance(display_name, str) or not display_name.strip():
        errors.append("display_name must be a non-empty string")

    if profile.get("integration_policy") != "EXTERNAL_PROVIDER":
        errors.append("integration_policy must be EXTERNAL_PROVIDER")

    proof_level = profile.get("proof_level")
    if proof_level not in PROOF_LEVELS:
        errors.append("proof_level is invalid")
    mode = profile.get("integration_mode")
    if mode not in INTEGRATION_MODES:
        errors.append("integration_mode is invalid")

    capabilities = profile.get("capabilities")
    if not is_sorted_unique_strings(capabilities, allowed=CAPABILITIES):
        errors.append("capabilities must be unique, lexically sorted C10 capability values")

    audit = profile.get("audit")
    _field_error(errors, "audit", audit, _AUDIT_FIELDS)
    if isinstance(audit, dict):
        audited_at = audit.get("audited_at")
        if not isinstance(audited_at, str) or _DATE_RE.fullmatch(audited_at) is None:
            errors.append("audit.audited_at must be an explicit ISO-like date or timestamp")
        evidence = audit.get("evidence")
        if not isinstance(evidence, list):
            errors.append("audit.evidence must be an array")
        else:
            for index, record in enumerate(evidence):
                label = f"audit.evidence[{index}]"
                _field_error(errors, label, record, _EVIDENCE_FIELDS)
                if not isinstance(record, dict):
                    continue
                if record.get("kind") not in EVIDENCE_KINDS:
                    errors.append(f"{label}.kind is invalid")
                if not _valid_locator(record.get("locator")):
                    errors.append(f"{label}.locator is invalid")
                observed_at = record.get("observed_at")
                if not isinstance(observed_at, str) or _DATE_RE.fullmatch(observed_at) is None:
                    errors.append(f"{label}.observed_at is invalid")
                if not is_sorted_unique_strings(record.get("supports")) or not record.get("supports"):
                    errors.append(f"{label}.supports must be a non-empty unique sorted string array")
                evidence_sha = record.get("sha256")
                if evidence_sha is not None and (
                    not isinstance(evidence_sha, str) or SHA256_RE.fullmatch(evidence_sha) is None
                ):
                    errors.append(f"{label}.sha256 must be null or lowercase SHA-256")

    api = profile.get("api")
    _field_error(errors, "api", api, _API_FIELDS)
    api_state = None
    if isinstance(api, dict):
        api_state = api.get("state")
        if api_state not in API_STATES:
            errors.append("api.state is invalid")
        if api.get("auth") not in API_AUTH:
            errors.append("api.auth is invalid")
        contract = api.get("official_contract")
        if api_state == "UNVERIFIED_API":
            if contract is not None:
                errors.append("api.official_contract must be null while API is unverified")
        elif api_state in API_STATES:
            _field_error(errors, "api.official_contract", contract, _CONTRACT_FIELDS)
            if isinstance(contract, dict):
                if contract.get("kind") not in API_CONTRACT_KINDS:
                    errors.append("api.official_contract.kind is invalid")
                for field in ("locator", "origin"):
                    value = contract.get(field)
                    if not isinstance(value, str) or not value.startswith("https://"):
                        errors.append(f"api.official_contract.{field} must be HTTPS")
                version = contract.get("version")
                if not isinstance(version, str) or not version:
                    errors.append("api.official_contract.version must be non-empty")
                if contract.get("protocol") != "HTTPS":
                    errors.append("api.official_contract.protocol must be HTTPS")

    handoff = profile.get("handoff")
    _field_error(errors, "handoff", handoff, _HANDOFF_FIELDS)
    if isinstance(handoff, dict):
        if not is_sorted_unique_strings(handoff.get("accepted_input_kinds"), allowed=ARTIFACT_KINDS):
            errors.append("handoff.accepted_input_kinds must be unique, sorted artifact kinds")
        if not is_sorted_unique_strings(handoff.get("output_artifact_kinds"), allowed=ARTIFACT_KINDS):
            errors.append("handoff.output_artifact_kinds must be unique, sorted artifact kinds")
        if not isinstance(handoff.get("manual_action_required"), bool):
            errors.append("handoff.manual_action_required must be boolean")
        if handoff.get("determinism") not in DETERMINISM:
            errors.append("handoff.determinism is invalid")

    limits = profile.get("limits")
    _field_error(errors, "limits", limits, _LIMIT_FIELDS)
    if isinstance(limits, dict):
        for field in _LIMIT_FIELDS:
            value = limits.get(field)
            if value is not None and not is_positive_int(value):
                errors.append(f"limits.{field} must be null or a positive integer")

    if proof_level == "EP0_DISCOVERED" and mode != "RESEARCH_ONLY":
        errors.append("EP0 providers must remain RESEARCH_ONLY")

    if mode == "RESEARCH_ONLY" and isinstance(limits, dict):
        if any(limits.get(field) is not None for field in _LIMIT_FIELDS):
            errors.append("RESEARCH_ONLY limits must remain null")

    if mode == "MANUAL_FILE_HANDOFF":
        if proof_level not in PROOF_LEVELS[1:]:
            errors.append("MANUAL_FILE_HANDOFF requires at least EP1_HANDOFF_VERIFIED")
        if isinstance(handoff, dict):
            if not handoff.get("accepted_input_kinds") or not handoff.get("output_artifact_kinds"):
                errors.append("MANUAL_FILE_HANDOFF requires proven input and output artifact kinds")
            if handoff.get("manual_action_required") is not True:
                errors.append("MANUAL_FILE_HANDOFF requires manual_action_required=true")
        if isinstance(limits, dict):
            if not is_positive_int(limits.get("max_input_bytes")):
                errors.append("MANUAL_FILE_HANDOFF requires a positive max_input_bytes")
            if not is_positive_int(limits.get("max_output_bytes")):
                errors.append("MANUAL_FILE_HANDOFF requires a positive max_output_bytes")
            if limits.get("timeout_seconds") is not None:
                errors.append("MANUAL_FILE_HANDOFF timeout_seconds must be null")

    if mode == "API_ADAPTER":
        if api_state not in {"CONTRACT_PROVEN_API", "SMOKE_PROVEN_API"}:
            errors.append("API_ADAPTER requires CONTRACT_PROVEN_API or SMOKE_PROVEN_API")
        if isinstance(limits, dict) and any(not is_positive_int(limits.get(field)) for field in _LIMIT_FIELDS):
            errors.append("API_ADAPTER requires positive max_input_bytes, max_output_bytes, and timeout_seconds")

    upstream = _upstream_external_providers(upstream_registry)
    if isinstance(provider_id, str):
        upstream_provider = upstream.get(provider_id)
        if upstream_provider is None:
            errors.append("provider_id is not registered by C0")
        else:
            if upstream_provider.get("integration_policy") != "EXTERNAL_PROVIDER":
                errors.append("upstream integration_policy must be EXTERNAL_PROVIDER")
            upstream_api_state = upstream_provider.get("api_state")
            if api_state != upstream_api_state:
                errors.append("profile api.state must be atomically reconciled with upstream api_state")

    digest = profile.get("profile_sha256")
    if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
        errors.append("profile_sha256 must be a lowercase SHA-256")
    elif digest != profile_fingerprint(profile):
        errors.append("profile_sha256 does not match canonical profile content")

    return errors


def validate_profile_catalog(documents: object, upstream_registry: object) -> list[str]:
    if not isinstance(documents, list):
        return ["provider profile catalog must be an array"]
    errors: list[str] = []
    seen: set[str] = set()
    for index, document in enumerate(documents):
        provider_id = document.get("provider_id") if isinstance(document, dict) else None
        if isinstance(provider_id, str):
            if provider_id in seen:
                errors.append(f"duplicate provider_id: {provider_id}")
            seen.add(provider_id)
        for error in validate_profile(document, upstream_registry):
            errors.append(f"profiles[{index}]: {error}")
    return sorted(errors)


def load_profile_catalog(
    profile_dir: Path,
    upstream_registry: dict[str, object],
) -> dict[str, dict[str, object]]:
    path = Path(profile_dir)
    if not path.is_dir():
        raise ValueError("C10 profile directory does not exist")
    documents: list[dict[str, object]] = []
    for profile_path in sorted(path.glob("*.json"), key=lambda item: item.name):
        try:
            document = json.loads(profile_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid C10 profile JSON: {profile_path.name}") from exc
        if not isinstance(document, dict):
            raise ValueError(f"C10 profile must be an object: {profile_path.name}")
        documents.append(document)

    errors = validate_profile_catalog(documents, upstream_registry)
    if errors:
        raise ValueError("invalid C10 provider catalog: " + "; ".join(errors))

    catalog: dict[str, dict[str, object]] = {}
    for document in sorted(documents, key=lambda value: value["provider_id"]):
        provider_id = document["provider_id"]
        catalog[provider_id] = copy.deepcopy(document)
    return catalog
