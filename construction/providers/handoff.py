from __future__ import annotations

import copy
from pathlib import PurePosixPath

from construction.providers.common import (
    ARTIFACT_KINDS,
    PROVIDER_ID_RE,
    SHA256_RE,
    canonical_json_bytes,
    sha256_hex,
)
from construction.providers.errors import C10Error
from construction.providers.profiles import profile_fingerprint

_REQUEST_FIELDS = {
    "schema_version",
    "request_id",
    "provider_id",
    "provider_profile_sha256",
    "mode",
    "operation",
    "text_input",
    "input_artifacts",
    "expected_output_kinds",
    "target",
    "manual_step",
}
_TARGET_FIELDS = {"minecraft", "loader", "physical_modlist_sha256"}
_ARTIFACT_FIELDS = {"kind", "sha256", "byte_length", "media_type", "repo_relpath"}
_MANUAL_STEP_FIELDS = {"required", "step_id", "instruction", "expected_result"}
_REQUEST_OPERATIONS = {
    "PROMPT_TO_STRUCTURE",
    "IMAGE_TO_STRUCTURE",
    "MESH_TO_STRUCTURE",
    "STRUCTURE_EDITING",
}
_STRUCTURE_ARTIFACT_KINDS = {"SCHEMATIC_FILE", "LITEMATIC_FILE", "VANILLA_STRUCTURE_NBT"}
_AUTOMATION_API_STATES = {"CONTRACT_PROVEN_API", "SMOKE_PROVEN_API"}

_RECEIPT_FIELDS = {
    "schema_version",
    "request_id",
    "provider_id",
    "provider_profile_sha256",
    "mode",
    "received_artifacts",
    "provider_metadata",
    "factory_validation",
    "receipt_sha256",
}
_FACTORY_VALIDATION_FIELDS = {"state", "validators"}
_VALIDATOR_FIELDS = {"stage", "authority", "artifact_sha256", "result", "evidence_ref"}
_VALIDATION_STATES = (
    "UNVALIDATED",
    "FORMAT_VALIDATED",
    "FACTORY_NORMALIZED",
    "GOLDEN_ACCEPTED",
)
_VALIDATOR_STAGES = ("FORMAT", "NORMALIZE", "GOLDEN")
_VALIDATOR_RESULTS = {"PASS", "FAIL"}
_STAGE_ORDER = {stage: index for index, stage in enumerate(_VALIDATOR_STAGES)}


def _error(code: str, message: str) -> str:
    return f"{code}: {message}"


def _request_fingerprint(request: dict[str, object]) -> str:
    payload = copy.deepcopy(request)
    payload.pop("request_id", None)
    return sha256_hex(canonical_json_bytes(payload))


def _receipt_fingerprint(receipt: dict[str, object]) -> str:
    payload = copy.deepcopy(receipt)
    payload.pop("receipt_sha256", None)
    return sha256_hex(canonical_json_bytes(payload))


def _is_non_empty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value) and len(value) <= 4000


def _is_repo_fixture_path(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/"):
        return False
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return False
    try:
        normalized = PurePosixPath(value).as_posix()
    except (TypeError, ValueError):
        return False
    return normalized == value and value.startswith("construction/fixtures/c10/")


def _is_evidence_ref(value: object) -> bool:
    prefix = "repo://construction/"
    if not isinstance(value, str) or not value.startswith(prefix) or "\\" in value:
        return False
    suffix = value[len(prefix):]
    if not suffix:
        return False
    parts = suffix.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return False
    try:
        normalized = PurePosixPath(suffix).as_posix()
    except (TypeError, ValueError):
        return False
    return normalized == suffix


def _validate_artifact_descriptor(artifact: object, index: int) -> list[str]:
    label = f"input_artifacts[{index}]"
    if not isinstance(artifact, dict):
        return [_error("INVALID_HANDOFF_REQUEST", f"{label} must be an object")]

    errors: list[str] = []
    if set(artifact) != _ARTIFACT_FIELDS:
        errors.append(_error("INVALID_HANDOFF_REQUEST", f"{label} fields do not match the C10 contract"))

    if artifact.get("kind") not in ARTIFACT_KINDS:
        errors.append(_error("ARTIFACT_KIND_UNSUPPORTED", f"{label}.kind is unsupported"))

    digest = artifact.get("sha256")
    if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
        errors.append(_error("INVALID_HANDOFF_REQUEST", f"{label}.sha256 must be lowercase SHA-256"))

    byte_length = artifact.get("byte_length")
    if not isinstance(byte_length, int) or isinstance(byte_length, bool) or byte_length <= 0:
        errors.append(_error("INVALID_HANDOFF_REQUEST", f"{label}.byte_length must be a positive integer"))

    media_type = artifact.get("media_type")
    if not isinstance(media_type, str) or not media_type:
        errors.append(_error("INVALID_HANDOFF_REQUEST", f"{label}.media_type must be non-empty"))

    if not _is_repo_fixture_path(artifact.get("repo_relpath")):
        errors.append(
            _error(
                "INVALID_HANDOFF_REQUEST",
                f"{label}.repo_relpath must be null or a normalized construction/fixtures/c10 path",
            )
        )
    return errors


def _validate_received_artifact_descriptor(artifact: object, index: int) -> list[str]:
    label = f"received_artifacts[{index}]"
    if not isinstance(artifact, dict):
        return [_error("INVALID_HANDOFF_RECEIPT", f"{label} must be an object")]

    errors: list[str] = []
    if set(artifact) != _ARTIFACT_FIELDS:
        errors.append(_error("INVALID_HANDOFF_RECEIPT", f"{label} fields do not match the C10 contract"))

    if artifact.get("kind") not in ARTIFACT_KINDS:
        errors.append(_error("ARTIFACT_KIND_UNSUPPORTED", f"{label}.kind is unsupported"))

    digest = artifact.get("sha256")
    if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
        errors.append(_error("INVALID_HANDOFF_RECEIPT", f"{label}.sha256 must be lowercase SHA-256"))

    byte_length = artifact.get("byte_length")
    if not isinstance(byte_length, int) or isinstance(byte_length, bool) or byte_length <= 0:
        errors.append(_error("INVALID_HANDOFF_RECEIPT", f"{label}.byte_length must be a positive integer"))

    media_type = artifact.get("media_type")
    if not isinstance(media_type, str) or not media_type:
        errors.append(_error("INVALID_HANDOFF_RECEIPT", f"{label}.media_type must be non-empty"))

    if not _is_repo_fixture_path(artifact.get("repo_relpath")):
        errors.append(
            _error(
                "INVALID_HANDOFF_RECEIPT",
                f"{label}.repo_relpath must be null or a normalized construction/fixtures/c10 path",
            )
        )
    return errors


def _validate_manual_step(value: object) -> list[str]:
    if not isinstance(value, dict):
        return [_error("MANUAL_ACTION_REQUIRED", "manual mode requires one manual_step object")]

    errors: list[str] = []
    if set(value) != _MANUAL_STEP_FIELDS:
        errors.append(_error("INVALID_HANDOFF_REQUEST", "manual_step fields do not match the C10 contract"))
    if value.get("required") is not True:
        errors.append(_error("MANUAL_ACTION_REQUIRED", "manual_step.required must be true"))
    for field in ("step_id", "instruction", "expected_result"):
        field_value = value.get(field)
        if not isinstance(field_value, str) or not field_value.strip():
            errors.append(_error("INVALID_HANDOFF_REQUEST", f"manual_step.{field} must be non-empty"))
    return errors


def validate_handoff_request(
    request: dict[str, object],
    profile: dict[str, object],
    *,
    current_physical_modlist_sha256: str | None = None,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(request, dict):
        return [_error("INVALID_HANDOFF_REQUEST", "request must be an object")]
    if not isinstance(profile, dict):
        return [_error("INVALID_PROVIDER_PROFILE", "profile must be an object")]

    if set(request) != _REQUEST_FIELDS:
        errors.append(_error("INVALID_HANDOFF_REQUEST", "request fields do not match the C10 contract"))
    if request.get("schema_version") != 1:
        errors.append(_error("INVALID_HANDOFF_REQUEST", "schema_version must be 1"))

    request_id = request.get("request_id")
    if not isinstance(request_id, str) or SHA256_RE.fullmatch(request_id) is None:
        errors.append(_error("INVALID_HANDOFF_REQUEST", "request_id must be lowercase SHA-256"))
    elif request_id != _request_fingerprint(request):
        errors.append(_error("INVALID_HANDOFF_REQUEST", "request_id does not match canonical request content"))

    profile_id = profile.get("provider_id")
    if request.get("provider_id") != profile_id:
        errors.append(_error("REQUEST_PROFILE_MISMATCH", "provider_id does not match the current profile"))

    current_profile_sha = profile.get("profile_sha256")
    if (
        not isinstance(current_profile_sha, str)
        or SHA256_RE.fullmatch(current_profile_sha) is None
        or current_profile_sha != profile_fingerprint(profile)
    ):
        errors.append(_error("INVALID_PROVIDER_PROFILE", "current provider profile fingerprint is invalid"))
    if request.get("provider_profile_sha256") != current_profile_sha:
        errors.append(_error("PROVIDER_DRIFT_DETECTED", "provider profile fingerprint changed after request creation"))

    mode = request.get("mode")
    profile_mode = profile.get("integration_mode")
    if mode != profile_mode:
        errors.append(_error("REQUEST_PROFILE_MISMATCH", "request mode does not match the current profile"))
    if profile_mode == "RESEARCH_ONLY" or mode == "RESEARCH_ONLY":
        errors.append(_error("INTEGRATION_MODE_NOT_ALLOWED", "RESEARCH_ONLY cannot create an operational request"))
    elif mode not in {"MANUAL_FILE_HANDOFF", "API_ADAPTER"}:
        errors.append(_error("INTEGRATION_MODE_NOT_ALLOWED", "request mode is not operationally supported"))

    operation = request.get("operation")
    if operation not in _REQUEST_OPERATIONS:
        errors.append(_error("INVALID_HANDOFF_REQUEST", "operation is not a C10 v1 request operation"))
    capabilities = profile.get("capabilities")
    if not isinstance(capabilities, list) or operation not in capabilities:
        errors.append(_error("CAPABILITY_NOT_PROVEN", "operation is not proven by the provider profile"))

    text_input = request.get("text_input")
    if text_input is not None and not isinstance(text_input, str):
        errors.append(_error("INVALID_HANDOFF_REQUEST", "text_input must be null or text"))
    elif isinstance(text_input, str) and (not text_input or len(text_input) > 4000):
        errors.append(_error("INVALID_HANDOFF_REQUEST", "text_input must be non-empty and at most 4000 characters"))

    input_artifacts = request.get("input_artifacts")
    artifacts: list[object]
    if not isinstance(input_artifacts, list):
        errors.append(_error("INVALID_HANDOFF_REQUEST", "input_artifacts must be an array"))
        artifacts = []
    else:
        artifacts = input_artifacts
        for index, artifact in enumerate(artifacts):
            errors.extend(_validate_artifact_descriptor(artifact, index))

    expected_output_kinds = request.get("expected_output_kinds")
    outputs: list[object]
    if not isinstance(expected_output_kinds, list) or not expected_output_kinds:
        errors.append(_error("INVALID_HANDOFF_REQUEST", "expected_output_kinds must be a non-empty array"))
        outputs = []
    else:
        outputs = expected_output_kinds
        if any(not isinstance(item, str) or item not in ARTIFACT_KINDS for item in outputs):
            errors.append(_error("ARTIFACT_KIND_UNSUPPORTED", "expected_output_kinds contains an unsupported kind"))
        if outputs != sorted(outputs) or len(outputs) != len(set(outputs)):
            errors.append(_error("INVALID_HANDOFF_REQUEST", "expected_output_kinds must be unique and lexically sorted"))

    handoff = profile.get("handoff")
    if not isinstance(handoff, dict):
        errors.append(_error("INVALID_PROVIDER_PROFILE", "profile handoff contract is missing"))
        accepted_kinds: list[object] = []
        output_kinds: list[object] = []
    else:
        accepted = handoff.get("accepted_input_kinds")
        declared_outputs = handoff.get("output_artifact_kinds")
        accepted_kinds = accepted if isinstance(accepted, list) else []
        output_kinds = declared_outputs if isinstance(declared_outputs, list) else []

    for artifact in artifacts:
        if isinstance(artifact, dict) and artifact.get("kind") not in accepted_kinds:
            errors.append(_error("ARTIFACT_KIND_UNSUPPORTED", "input artifact kind is not accepted by the provider profile"))
    for output_kind in outputs:
        if output_kind not in output_kinds:
            errors.append(_error("ARTIFACT_KIND_UNSUPPORTED", "expected output kind is not declared by the provider profile"))

    artifact_kinds = [artifact.get("kind") for artifact in artifacts if isinstance(artifact, dict)]
    if operation == "PROMPT_TO_STRUCTURE":
        if not _is_non_empty_text(text_input) or artifacts:
            errors.append(_error("INVALID_HANDOFF_REQUEST", "PROMPT_TO_STRUCTURE requires text only"))
    elif operation == "IMAGE_TO_STRUCTURE":
        if len(artifacts) != 1 or artifact_kinds != ["IMAGE"]:
            errors.append(_error("INVALID_HANDOFF_REQUEST", "IMAGE_TO_STRUCTURE requires exactly one IMAGE artifact"))
        if text_input is not None and not _is_non_empty_text(text_input):
            errors.append(_error("INVALID_HANDOFF_REQUEST", "IMAGE_TO_STRUCTURE optional text must be non-empty and at most 4000 characters"))
    elif operation == "MESH_TO_STRUCTURE":
        if len(artifacts) != 1 or artifact_kinds != ["MESH"] or text_input is not None:
            errors.append(_error("INVALID_HANDOFF_REQUEST", "MESH_TO_STRUCTURE requires exactly one MESH artifact and null text_input"))
    elif operation == "STRUCTURE_EDITING":
        if (
            len(artifacts) != 1
            or not artifact_kinds
            or artifact_kinds[0] not in _STRUCTURE_ARTIFACT_KINDS
            or not _is_non_empty_text(text_input)
        ):
            errors.append(
                _error(
                    "INVALID_HANDOFF_REQUEST",
                    "STRUCTURE_EDITING requires one structure artifact and a non-empty edit instruction",
                )
            )

    target = request.get("target")
    if not isinstance(target, dict):
        errors.append(_error("INVALID_HANDOFF_REQUEST", "target must be an object"))
    else:
        if set(target) != _TARGET_FIELDS:
            errors.append(_error("INVALID_HANDOFF_REQUEST", "target fields do not match the C10 contract"))
        if target.get("minecraft") != "1.21.1":
            errors.append(_error("INVALID_HANDOFF_REQUEST", "target.minecraft must be 1.21.1"))
        if target.get("loader") != "neoforge":
            errors.append(_error("INVALID_HANDOFF_REQUEST", "target.loader must be neoforge"))
        physical_sha = target.get("physical_modlist_sha256")
        if not isinstance(physical_sha, str) or SHA256_RE.fullmatch(physical_sha) is None:
            errors.append(_error("INVALID_HANDOFF_REQUEST", "target.physical_modlist_sha256 must be lowercase SHA-256"))
        if current_physical_modlist_sha256 is not None:
            if SHA256_RE.fullmatch(current_physical_modlist_sha256) is None:
                errors.append(_error("INVALID_HANDOFF_REQUEST", "current physical modlist fingerprint must be lowercase SHA-256"))
            elif physical_sha != current_physical_modlist_sha256:
                errors.append(_error("PROVIDER_DRIFT_DETECTED", "physical modlist evidence is stale"))

    manual_step = request.get("manual_step")
    if mode == "MANUAL_FILE_HANDOFF":
        errors.extend(_validate_manual_step(manual_step))
        if isinstance(handoff, dict) and handoff.get("manual_action_required") is not True:
            errors.append(_error("MANUAL_ACTION_REQUIRED", "provider profile must require manual action in manual mode"))
    elif mode == "API_ADAPTER":
        if manual_step is not None:
            errors.append(_error("INVALID_HANDOFF_REQUEST", "API_ADAPTER requires manual_step=null"))
        api = profile.get("api")
        api_state = api.get("state") if isinstance(api, dict) else None
        if api_state not in _AUTOMATION_API_STATES:
            errors.append(_error("UNVERIFIED_API", "API_ADAPTER requires CONTRACT_PROVEN_API or SMOKE_PROVEN_API"))

    return errors


def build_handoff_request(
    profile: dict[str, object],
    *,
    operation: str,
    text_input: str | None,
    input_artifacts: list[dict[str, object]],
    expected_output_kinds: list[str],
    physical_modlist_sha256: str,
    manual_step: dict[str, object] | None,
) -> dict[str, object]:
    if not isinstance(profile, dict):
        raise C10Error("INVALID_HANDOFF_REQUEST", "handoff request rejected: profile must be an object")

    request: dict[str, object] = {
        "schema_version": 1,
        "request_id": "",
        "provider_id": profile.get("provider_id"),
        "provider_profile_sha256": profile.get("profile_sha256"),
        "mode": profile.get("integration_mode"),
        "operation": operation,
        "text_input": text_input,
        "input_artifacts": copy.deepcopy(input_artifacts),
        "expected_output_kinds": copy.deepcopy(expected_output_kinds),
        "target": {
            "minecraft": "1.21.1",
            "loader": "neoforge",
            "physical_modlist_sha256": physical_modlist_sha256,
        },
        "manual_step": copy.deepcopy(manual_step),
    }
    request["request_id"] = _request_fingerprint(request)
    errors = validate_handoff_request(request, profile)
    if errors:
        raise C10Error("INVALID_HANDOFF_REQUEST", "handoff request rejected: " + "; ".join(errors))
    return request


def _validate_validator_record(record: object, index: int, artifact_shas: set[str]) -> list[str]:
    label = f"factory_validation.validators[{index}]"
    if not isinstance(record, dict):
        return [_error("INVALID_HANDOFF_RECEIPT", f"{label} must be an object")]

    errors: list[str] = []
    if set(record) != _VALIDATOR_FIELDS:
        errors.append(_error("INVALID_HANDOFF_RECEIPT", f"{label} fields do not match the C10 contract"))

    stage = record.get("stage")
    if stage not in _VALIDATOR_STAGES:
        errors.append(_error("INVALID_HANDOFF_RECEIPT", f"{label}.stage is invalid"))

    authority = record.get("authority")
    if not isinstance(authority, str) or not authority.strip():
        errors.append(_error("INVALID_HANDOFF_RECEIPT", f"{label}.authority must be non-empty"))

    artifact_sha = record.get("artifact_sha256")
    if not isinstance(artifact_sha, str) or SHA256_RE.fullmatch(artifact_sha) is None:
        errors.append(_error("INVALID_HANDOFF_RECEIPT", f"{label}.artifact_sha256 must be lowercase SHA-256"))
    elif artifact_sha not in artifact_shas:
        errors.append(_error("INVALID_HANDOFF_RECEIPT", f"{label}.artifact_sha256 is not a received artifact"))

    if record.get("result") not in _VALIDATOR_RESULTS:
        errors.append(_error("INVALID_HANDOFF_RECEIPT", f"{label}.result must be PASS or FAIL"))

    if not _is_evidence_ref(record.get("evidence_ref")):
        errors.append(
            _error(
                "INVALID_HANDOFF_RECEIPT",
                f"{label}.evidence_ref must be a normalized repo://construction/ locator",
            )
        )
    return errors


def _validator_sort_key(record: dict[str, object]) -> tuple[object, ...]:
    stage = record.get("stage")
    return (
        _STAGE_ORDER.get(stage, len(_STAGE_ORDER)),
        str(record.get("authority", "")),
        str(record.get("artifact_sha256", "")),
        str(record.get("result", "")),
        str(record.get("evidence_ref", "")),
    )


def _required_validation_errors(
    state: object,
    validators: list[dict[str, object]],
    artifact_shas: set[str],
) -> list[str]:
    errors: list[str] = []
    if state not in _VALIDATION_STATES:
        return [_error("INVALID_HANDOFF_RECEIPT", "factory_validation.state is invalid")]

    state_index = _VALIDATION_STATES.index(state)
    if state_index >= 1:
        format_pass = {
            record.get("artifact_sha256")
            for record in validators
            if record.get("stage") == "FORMAT" and record.get("result") == "PASS"
        }
        missing = sorted(artifact_shas - format_pass)
        if missing:
            errors.append(
                _error(
                    "FORMAT_VALIDATION_FAILED",
                    "FORMAT/PASS evidence is required for every received artifact",
                )
            )
    if state_index >= 2 and not any(
        record.get("stage") == "NORMALIZE" and record.get("result") == "PASS"
        for record in validators
    ):
        errors.append(
            _error(
                "INVALID_HANDOFF_RECEIPT",
                "NORMALIZE/PASS evidence is required before FACTORY_NORMALIZED",
            )
        )
    if state_index >= 3 and not any(
        record.get("stage") == "GOLDEN" and record.get("result") == "PASS"
        for record in validators
    ):
        errors.append(
            _error(
                "INVALID_HANDOFF_RECEIPT",
                "GOLDEN/PASS evidence is required before GOLDEN_ACCEPTED",
            )
        )
    return errors


def _validate_receipt_structure(receipt: object) -> list[str]:
    if not isinstance(receipt, dict):
        return [_error("INVALID_HANDOFF_RECEIPT", "receipt must be an object")]

    errors: list[str] = []
    if set(receipt) != _RECEIPT_FIELDS:
        errors.append(_error("INVALID_HANDOFF_RECEIPT", "receipt fields do not match the C10 contract"))
    if receipt.get("schema_version") != 1:
        errors.append(_error("INVALID_HANDOFF_RECEIPT", "schema_version must be 1"))

    request_id = receipt.get("request_id")
    if not isinstance(request_id, str) or SHA256_RE.fullmatch(request_id) is None:
        errors.append(_error("INVALID_HANDOFF_RECEIPT", "request_id must be lowercase SHA-256"))

    provider_id = receipt.get("provider_id")
    if not isinstance(provider_id, str) or PROVIDER_ID_RE.fullmatch(provider_id) is None:
        errors.append(_error("INVALID_HANDOFF_RECEIPT", "provider_id must be a lowercase stable identifier"))

    profile_sha = receipt.get("provider_profile_sha256")
    if not isinstance(profile_sha, str) or SHA256_RE.fullmatch(profile_sha) is None:
        errors.append(_error("INVALID_HANDOFF_RECEIPT", "provider_profile_sha256 must be lowercase SHA-256"))

    if receipt.get("mode") not in {"MANUAL_FILE_HANDOFF", "API_ADAPTER"}:
        errors.append(_error("INVALID_HANDOFF_RECEIPT", "mode is not an operational C10 integration mode"))

    received_artifacts = receipt.get("received_artifacts")
    artifacts: list[object]
    if not isinstance(received_artifacts, list):
        errors.append(_error("INVALID_HANDOFF_RECEIPT", "received_artifacts must be an array"))
        artifacts = []
    else:
        artifacts = received_artifacts
        for index, artifact in enumerate(artifacts):
            errors.extend(_validate_received_artifact_descriptor(artifact, index))

    if receipt.get("provider_metadata") != {}:
        errors.append(_error("INVALID_HANDOFF_RECEIPT", "provider_metadata must be exactly {} in C10 v1"))

    artifact_shas = {
        artifact.get("sha256")
        for artifact in artifacts
        if isinstance(artifact, dict)
        and isinstance(artifact.get("sha256"), str)
        and SHA256_RE.fullmatch(artifact["sha256"]) is not None
    }

    validation = receipt.get("factory_validation")
    validators: list[dict[str, object]] = []
    state: object = None
    if not isinstance(validation, dict):
        errors.append(_error("INVALID_HANDOFF_RECEIPT", "factory_validation must be an object"))
    else:
        if set(validation) != _FACTORY_VALIDATION_FIELDS:
            errors.append(_error("INVALID_HANDOFF_RECEIPT", "factory_validation fields do not match the C10 contract"))
        state = validation.get("state")
        raw_validators = validation.get("validators")
        if not isinstance(raw_validators, list):
            errors.append(_error("INVALID_HANDOFF_RECEIPT", "factory_validation.validators must be an array"))
        else:
            for index, record in enumerate(raw_validators):
                errors.extend(_validate_validator_record(record, index, artifact_shas))
                if isinstance(record, dict):
                    validators.append(record)
        errors.extend(_required_validation_errors(state, validators, artifact_shas))

    receipt_sha = receipt.get("receipt_sha256")
    if not isinstance(receipt_sha, str) or SHA256_RE.fullmatch(receipt_sha) is None:
        errors.append(_error("INVALID_HANDOFF_RECEIPT", "receipt_sha256 must be lowercase SHA-256"))
    elif receipt_sha != _receipt_fingerprint(receipt):
        errors.append(_error("INVALID_HANDOFF_RECEIPT", "receipt_sha256 does not match canonical receipt content"))

    return errors


def validate_handoff_receipt(
    receipt: dict[str, object],
    request: dict[str, object],
    profile: dict[str, object],
) -> list[str]:
    errors = _validate_receipt_structure(receipt)
    if not isinstance(receipt, dict) or not isinstance(request, dict) or not isinstance(profile, dict):
        if not isinstance(request, dict):
            errors.append(_error("INVALID_HANDOFF_REQUEST", "request must be an object"))
        if not isinstance(profile, dict):
            errors.append(_error("INVALID_PROVIDER_PROFILE", "profile must be an object"))
        return errors

    request_errors = validate_handoff_request(request, profile)
    errors.extend(request_errors)

    if receipt.get("request_id") != request.get("request_id"):
        errors.append(_error("REQUEST_PROFILE_MISMATCH", "receipt request_id does not match the request"))
    if receipt.get("provider_id") != request.get("provider_id"):
        errors.append(_error("REQUEST_PROFILE_MISMATCH", "receipt provider_id does not match the request"))
    if receipt.get("mode") != request.get("mode"):
        errors.append(_error("REQUEST_PROFILE_MISMATCH", "receipt mode does not match the request"))
    if receipt.get("provider_profile_sha256") != request.get("provider_profile_sha256"):
        errors.append(
            _error(
                "REQUEST_PROFILE_MISMATCH",
                "receipt provider_profile_sha256 does not match the request",
            )
        )

    current_profile_sha = profile.get("profile_sha256")
    if (
        not isinstance(current_profile_sha, str)
        or SHA256_RE.fullmatch(current_profile_sha) is None
        or current_profile_sha != profile_fingerprint(profile)
    ):
        errors.append(_error("INVALID_PROVIDER_PROFILE", "current provider profile fingerprint is invalid"))
    elif receipt.get("provider_profile_sha256") != current_profile_sha:
        errors.append(
            _error(
                "PROVIDER_DRIFT_DETECTED",
                "provider profile fingerprint changed after receipt creation",
            )
        )

    expected_output_kinds = request.get("expected_output_kinds")
    allowed_outputs = set(expected_output_kinds) if isinstance(expected_output_kinds, list) else set()
    received_artifacts = receipt.get("received_artifacts")
    if isinstance(received_artifacts, list):
        for artifact in received_artifacts:
            if isinstance(artifact, dict) and artifact.get("kind") not in allowed_outputs:
                errors.append(
                    _error(
                        "ARTIFACT_KIND_UNSUPPORTED",
                        "received artifact kind is not permitted by expected_output_kinds",
                    )
                )

    return errors


def build_handoff_receipt(
    request: dict[str, object],
    profile: dict[str, object],
    *,
    received_artifacts: list[dict[str, object]],
) -> dict[str, object]:
    request_errors = validate_handoff_request(request, profile)
    if request_errors:
        raise C10Error(
            "INVALID_HANDOFF_RECEIPT",
            "handoff receipt rejected: request/profile contract is invalid; " + "; ".join(request_errors),
        )

    receipt: dict[str, object] = {
        "schema_version": 1,
        "request_id": request.get("request_id"),
        "provider_id": request.get("provider_id"),
        "provider_profile_sha256": request.get("provider_profile_sha256"),
        "mode": request.get("mode"),
        "received_artifacts": copy.deepcopy(received_artifacts),
        "provider_metadata": {},
        "factory_validation": {
            "state": "UNVALIDATED",
            "validators": [],
        },
        "receipt_sha256": "",
    }
    receipt["receipt_sha256"] = _receipt_fingerprint(receipt)
    errors = validate_handoff_receipt(receipt, request, profile)
    if errors:
        raise C10Error("INVALID_HANDOFF_RECEIPT", "handoff receipt rejected: " + "; ".join(errors))
    return receipt


def advance_validation_state(
    receipt: dict[str, object],
    new_state: str,
    validators: list[dict[str, object]],
) -> dict[str, object]:
    current_errors = _validate_receipt_structure(receipt)
    if current_errors:
        raise C10Error(
            "INVALID_HANDOFF_RECEIPT",
            "validation state cannot advance from an invalid receipt: " + "; ".join(current_errors),
        )
    if new_state not in _VALIDATION_STATES:
        raise C10Error("INVALID_HANDOFF_RECEIPT", "validation state is unknown")
    if not isinstance(validators, list):
        raise C10Error("INVALID_HANDOFF_RECEIPT", "validators must be an array")

    current_validation = receipt["factory_validation"]
    assert isinstance(current_validation, dict)
    current_state = current_validation["state"]
    assert current_state in _VALIDATION_STATES
    current_index = _VALIDATION_STATES.index(current_state)
    target_index = _VALIDATION_STATES.index(new_state)
    if target_index != current_index + 1:
        expected = _VALIDATION_STATES[current_index + 1] if current_index + 1 < len(_VALIDATION_STATES) else "no further state"
        raise C10Error(
            "INVALID_HANDOFF_RECEIPT",
            f"validation state may not skip or repeat; expected {expected}",
        )

    received_artifacts = receipt["received_artifacts"]
    assert isinstance(received_artifacts, list)
    artifact_shas = {
        artifact["sha256"]
        for artifact in received_artifacts
        if isinstance(artifact, dict) and isinstance(artifact.get("sha256"), str)
    }

    incoming: list[dict[str, object]] = []
    incoming_errors: list[str] = []
    for index, record in enumerate(validators):
        incoming_errors.extend(_validate_validator_record(record, index, artifact_shas))
        if isinstance(record, dict):
            incoming.append(copy.deepcopy(record))
    if incoming_errors:
        raise C10Error("INVALID_HANDOFF_RECEIPT", "; ".join(incoming_errors))
    if any(record.get("result") == "FAIL" for record in incoming):
        required_stage = _VALIDATOR_STAGES[target_index - 1]
        raise C10Error(
            "INVALID_HANDOFF_RECEIPT",
            f"{required_stage}/PASS evidence is required; FAIL evidence cannot advance state",
        )

    existing = current_validation["validators"]
    assert isinstance(existing, list)
    merged = [copy.deepcopy(record) for record in existing if isinstance(record, dict)] + incoming
    merged.sort(key=_validator_sort_key)

    candidate = copy.deepcopy(receipt)
    candidate_validation = candidate["factory_validation"]
    assert isinstance(candidate_validation, dict)
    candidate_validation["state"] = new_state
    candidate_validation["validators"] = merged
    candidate["receipt_sha256"] = _receipt_fingerprint(candidate)

    errors = _validate_receipt_structure(candidate)
    if errors:
        raise C10Error("INVALID_HANDOFF_RECEIPT", "validation state rejected: " + "; ".join(errors))
    return candidate
