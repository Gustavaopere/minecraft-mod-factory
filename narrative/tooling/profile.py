from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


@dataclass(frozen=True)
class DialogueReferenceRule:
    allowed_types: tuple[str, ...]
    min_references: int


@dataclass(frozen=True)
class EntityReferenceRule:
    allowed_types: tuple[str, ...]
    min_references: int


@dataclass(frozen=True)
class AuxiliaryReferenceRule:
    allowed_types: tuple[str, ...]
    min_references: int


@dataclass(frozen=True)
class AuxiliaryDocumentContract:
    include: tuple[str, ...]
    required_sections: dict[str, tuple[str, ...]]
    reference_rules: dict[str, AuxiliaryReferenceRule]


@dataclass(frozen=True)
class NarrativeProfile:
    story_root: str
    dialogue_root: str
    entity_types: tuple[str, ...]
    editorial_state_prefixes: tuple[str, ...]
    editorial_state_headings: tuple[str, ...]
    dialogue_required_sections: dict[str, tuple[str, ...]]
    dialogue_entity_type: str
    dialogue_reference_rules: dict[str, DialogueReferenceRule]
    entity_required_sections: dict[str, dict[str, tuple[str, ...]]]
    entity_reference_rules: dict[str, dict[str, EntityReferenceRule]]
    auxiliary_document_contracts: dict[str, AuxiliaryDocumentContract]


def _strings(value, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f'{field} must be a non-empty list of strings')
    return tuple(item.strip() for item in value)


def resolve_workspace_path(path: str | Path, workspace_root: str | Path) -> Path:
    workspace = Path(workspace_root).resolve(strict=True)
    supplied = Path(path)
    candidate = supplied if supplied.is_absolute() else workspace / supplied
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise ValueError('path is outside the trusted workspace') from exc
    return resolved


def _reference_rules(data, sections: dict[str, tuple[str, ...]], entity_types: tuple[str, ...]) -> dict[str, DialogueReferenceRule]:
    raw_rules = data.get('dialogue_reference_rules', {})
    if not isinstance(raw_rules, dict):
        raise ValueError('dialogue_reference_rules must be an object')
    rules: dict[str, DialogueReferenceRule] = {}
    for key, raw_rule in raw_rules.items():
        if not isinstance(key, str) or key not in sections:
            raise ValueError('dialogue_reference_rules keys must name dialogue_required_sections')
        if not isinstance(raw_rule, dict):
            raise ValueError(f'dialogue_reference_rules.{key} must be an object')
        allowed_types = _strings(raw_rule.get('allowed_types'), f'dialogue_reference_rules.{key}.allowed_types')
        if any(entity_type not in entity_types for entity_type in allowed_types):
            raise ValueError(f'dialogue_reference_rules.{key}.allowed_types must be entity_types')
        min_references = raw_rule.get('min_references', 0)
        if isinstance(min_references, bool) or not isinstance(min_references, int) or min_references < 0:
            raise ValueError(f'dialogue_reference_rules.{key}.min_references must be a non-negative integer')
        rules[key] = DialogueReferenceRule(allowed_types=allowed_types, min_references=min_references)
    return rules


def _entity_required_sections(data, entity_types: tuple[str, ...]) -> dict[str, dict[str, tuple[str, ...]]]:
    raw_types = data.get('entity_required_sections', {})
    if not isinstance(raw_types, dict):
        raise ValueError('entity_required_sections must be an object')
    required: dict[str, dict[str, tuple[str, ...]]] = {}
    for entity_type, raw_sections in raw_types.items():
        if not isinstance(entity_type, str) or entity_type not in entity_types:
            raise ValueError('entity_required_sections keys must be entity_types')
        if not isinstance(raw_sections, dict) or not raw_sections:
            raise ValueError(f'entity_required_sections.{entity_type} must be a non-empty object')
        sections: dict[str, tuple[str, ...]] = {}
        for key, aliases in raw_sections.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError(f'entity_required_sections.{entity_type} keys must be non-empty strings')
            normalized_key = key.strip()
            sections[normalized_key] = _strings(
                aliases,
                f'entity_required_sections.{entity_type}.{normalized_key}',
            )
        required[entity_type] = sections
    return required


def _entity_reference_rules(
    data,
    required_sections: dict[str, dict[str, tuple[str, ...]]],
    entity_types: tuple[str, ...],
) -> dict[str, dict[str, EntityReferenceRule]]:
    raw_types = data.get('entity_reference_rules', {})
    if not isinstance(raw_types, dict):
        raise ValueError('entity_reference_rules must be an object')
    rules: dict[str, dict[str, EntityReferenceRule]] = {}
    for entity_type, raw_rules in raw_types.items():
        if not isinstance(entity_type, str) or entity_type not in entity_types:
            raise ValueError('entity_reference_rules keys must be entity_types')
        if not isinstance(raw_rules, dict) or not raw_rules:
            raise ValueError(f'entity_reference_rules.{entity_type} must be a non-empty object')
        declared_sections = required_sections.get(entity_type, {})
        typed_rules: dict[str, EntityReferenceRule] = {}
        for key, raw_rule in raw_rules.items():
            if not isinstance(key, str) or key not in declared_sections:
                raise ValueError(
                    f'entity_reference_rules.{entity_type} keys must name '
                    f'entity_required_sections.{entity_type}'
                )
            if not isinstance(raw_rule, dict):
                raise ValueError(f'entity_reference_rules.{entity_type}.{key} must be an object')
            allowed_types = _strings(
                raw_rule.get('allowed_types'),
                f'entity_reference_rules.{entity_type}.{key}.allowed_types',
            )
            if any(allowed_type not in entity_types for allowed_type in allowed_types):
                raise ValueError(
                    f'entity_reference_rules.{entity_type}.{key}.allowed_types must be entity_types'
                )
            min_references = raw_rule.get('min_references', 0)
            if isinstance(min_references, bool) or not isinstance(min_references, int) or min_references < 0:
                raise ValueError(
                    f'entity_reference_rules.{entity_type}.{key}.min_references '
                    'must be a non-negative integer'
                )
            typed_rules[key] = EntityReferenceRule(
                allowed_types=allowed_types,
                min_references=min_references,
            )
        rules[entity_type] = typed_rules
    return rules


def _auxiliary_document_contracts(
    data,
    entity_types: tuple[str, ...],
) -> dict[str, AuxiliaryDocumentContract]:
    raw_contracts = data.get('auxiliary_document_contracts', {})
    if not isinstance(raw_contracts, dict):
        raise ValueError('auxiliary_document_contracts must be an object')

    contracts: dict[str, AuxiliaryDocumentContract] = {}
    for raw_name, raw_contract in raw_contracts.items():
        if not isinstance(raw_name, str) or not raw_name.strip():
            raise ValueError('auxiliary_document_contracts keys must be non-empty strings')
        name = raw_name.strip()
        if name in contracts:
            raise ValueError('auxiliary_document_contracts keys must be unique after trimming')
        if not isinstance(raw_contract, dict) or not raw_contract:
            raise ValueError(f'auxiliary_document_contracts.{name} must be a non-empty object')

        include = _strings(raw_contract.get('include'), f'auxiliary_document_contracts.{name}.include')
        for pattern in include:
            pure = PurePosixPath(pattern)
            if '\\' in pattern or pure.is_absolute() or '..' in pure.parts:
                raise ValueError(
                    f'auxiliary_document_contracts.{name}.include patterns must be relative, use / separators, and not contain ..'
                )

        raw_sections = raw_contract.get('required_sections')
        if not isinstance(raw_sections, dict) or not raw_sections:
            raise ValueError(f'auxiliary_document_contracts.{name}.required_sections must be a non-empty object')
        required_sections: dict[str, tuple[str, ...]] = {}
        for raw_key, aliases in raw_sections.items():
            if not isinstance(raw_key, str) or not raw_key.strip():
                raise ValueError(
                    f'auxiliary_document_contracts.{name}.required_sections keys must be non-empty strings'
                )
            key = raw_key.strip()
            required_sections[key] = _strings(
                aliases,
                f'auxiliary_document_contracts.{name}.required_sections.{key}',
            )

        raw_rules = raw_contract.get('reference_rules', {})
        if not isinstance(raw_rules, dict):
            raise ValueError(f'auxiliary_document_contracts.{name}.reference_rules must be an object')
        reference_rules: dict[str, AuxiliaryReferenceRule] = {}
        for raw_key, raw_rule in raw_rules.items():
            if not isinstance(raw_key, str) or raw_key not in required_sections:
                raise ValueError(
                    f'auxiliary_document_contracts.{name}.reference_rules keys must name required_sections'
                )
            key = raw_key
            if not isinstance(raw_rule, dict):
                raise ValueError(f'auxiliary_document_contracts.{name}.reference_rules.{key} must be an object')
            allowed_types = _strings(
                raw_rule.get('allowed_types'),
                f'auxiliary_document_contracts.{name}.reference_rules.{key}.allowed_types',
            )
            if any(allowed_type not in entity_types for allowed_type in allowed_types):
                raise ValueError(
                    f'auxiliary_document_contracts.{name}.reference_rules.{key}.allowed_types must be entity_types'
                )
            min_references = raw_rule.get('min_references', 0)
            if isinstance(min_references, bool) or not isinstance(min_references, int) or min_references < 0:
                raise ValueError(
                    f'auxiliary_document_contracts.{name}.reference_rules.{key}.min_references '
                    'must be a non-negative integer'
                )
            reference_rules[key] = AuxiliaryReferenceRule(
                allowed_types=allowed_types,
                min_references=min_references,
            )

        contracts[name] = AuxiliaryDocumentContract(
            include=include,
            required_sections=required_sections,
            reference_rules=reference_rules,
        )

    return contracts


def load_profile(path: str | Path, workspace_root: str | Path | None = None) -> NarrativeProfile:
    workspace = Path.cwd() if workspace_root is None else workspace_root
    profile_path = resolve_workspace_path(path, workspace)
    data = json.loads(profile_path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('profile root must be an object')
    story_root = data.get('story_root')
    dialogue_root = data.get('dialogue_root')
    if not isinstance(story_root, str) or not story_root.strip():
        raise ValueError('story_root must be a non-empty string')
    if not isinstance(dialogue_root, str) or not dialogue_root.strip():
        raise ValueError('dialogue_root must be a non-empty string')
    entity_types = _strings(data.get('entity_types'), 'entity_types')
    state_prefixes = _strings(data.get('editorial_state_prefixes'), 'editorial_state_prefixes')
    state_headings = _strings(data.get('editorial_state_headings', ['Editorial state']), 'editorial_state_headings')
    raw_sections = data.get('dialogue_required_sections')
    if not isinstance(raw_sections, dict) or not raw_sections:
        raise ValueError('dialogue_required_sections must be a non-empty object')
    sections: dict[str, tuple[str, ...]] = {}
    for key, aliases in raw_sections.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError('dialogue_required_sections keys must be non-empty strings')
        sections[key.strip()] = _strings(aliases, f'dialogue_required_sections.{key}')
    dialogue_entity_type = data.get('dialogue_entity_type', 'DLG')
    if dialogue_entity_type not in entity_types:
        raise ValueError('dialogue_entity_type must be one of entity_types')
    reference_rules = _reference_rules(data, sections, entity_types)
    entity_sections = _entity_required_sections(data, entity_types)
    entity_reference_rules = _entity_reference_rules(data, entity_sections, entity_types)
    auxiliary_contracts = _auxiliary_document_contracts(data, entity_types)
    return NarrativeProfile(
        story_root=story_root.strip(),
        dialogue_root=dialogue_root.strip(),
        entity_types=entity_types,
        editorial_state_prefixes=state_prefixes,
        editorial_state_headings=state_headings,
        dialogue_required_sections=sections,
        dialogue_entity_type=dialogue_entity_type,
        dialogue_reference_rules=reference_rules,
        entity_required_sections=entity_sections,
        entity_reference_rules=entity_reference_rules,
        auxiliary_document_contracts=auxiliary_contracts,
    )
