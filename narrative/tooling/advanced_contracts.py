from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True)
class SectionReferenceRule:
    allowed_types: tuple[str, ...]
    min_references: int


@dataclass(frozen=True)
class KnowledgeEvidenceContract:
    include: tuple[str, ...]
    required_sections: dict[str, tuple[str, ...]]
    knowledge_state_sections: dict[str, tuple[str, ...]]
    reference_rules: dict[str, SectionReferenceRule]


@dataclass(frozen=True)
class RelationshipMemoryContract:
    include: tuple[str, ...]
    required_sections: dict[str, tuple[str, ...]]
    dimension_sections: dict[str, tuple[str, ...]]
    reference_rules: dict[str, SectionReferenceRule]
    source_actor_section: str | None
    target_actor_section: str | None
    memory_event_section: str | None
    kind_section: str | None
    allowed_kinds: tuple[str, ...]
    autonomy_section: str | None
    allowed_autonomy_states: tuple[str, ...]
    allow_self_relation: bool


@dataclass(frozen=True)
class ChronologyContract:
    event_types: tuple[str, ...]
    before_headings: tuple[str, ...]
    after_headings: tuple[str, ...]
    causes_headings: tuple[str, ...]
    caused_by_headings: tuple[str, ...]
    causality_acyclic: bool


@dataclass(frozen=True)
class AdvancedContracts:
    knowledge_evidence_contracts: dict[str, KnowledgeEvidenceContract]
    relationship_memory_contracts: dict[str, RelationshipMemoryContract]
    chronology_contract: ChronologyContract | None


def _strings(value, field: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f'{field} must be a list of strings')
    if not allow_empty and not value:
        raise ValueError(f'{field} must be a non-empty list of strings')
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f'{field} must contain only non-empty strings')
    return tuple(item.strip() for item in value)


def _include_patterns(value, field: str) -> tuple[str, ...]:
    patterns = _strings(value, field)
    for pattern in patterns:
        pure = PurePosixPath(pattern)
        if '\\' in pattern or pure.is_absolute() or '..' in pure.parts:
            raise ValueError(f'{field} patterns must be relative, use / separators, and not contain ..')
    return patterns


def _sections(value, field: str, *, allow_empty: bool = False) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, dict) or (not value and not allow_empty):
        qualifier = 'an object' if allow_empty else 'a non-empty object'
        raise ValueError(f'{field} must be {qualifier}')
    result: dict[str, tuple[str, ...]] = {}
    seen_aliases: dict[str, str] = {}
    for raw_key, aliases in value.items():
        if not isinstance(raw_key, str) or not raw_key.strip():
            raise ValueError(f'{field} keys must be non-empty strings')
        key = raw_key.strip()
        normalized = _strings(aliases, f'{field}.{key}')
        for alias in normalized:
            folded = alias.casefold()
            previous = seen_aliases.get(folded)
            if previous is not None and previous != key:
                raise ValueError(f'{field} aliases must not overlap between logical sections')
            seen_aliases[folded] = key
        result[key] = normalized
    return result


def _reference_rules(value, field: str, sections: set[str], entity_types: tuple[str, ...]) -> dict[str, SectionReferenceRule]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f'{field} must be an object')
    result: dict[str, SectionReferenceRule] = {}
    for raw_key, raw_rule in value.items():
        if not isinstance(raw_key, str) or raw_key not in sections:
            raise ValueError(f'{field} keys must name declared logical sections')
        if not isinstance(raw_rule, dict):
            raise ValueError(f'{field}.{raw_key} must be an object')
        allowed_types = _strings(raw_rule.get('allowed_types'), f'{field}.{raw_key}.allowed_types')
        if any(item not in entity_types for item in allowed_types):
            raise ValueError(f'{field}.{raw_key}.allowed_types must be entity_types')
        minimum = raw_rule.get('min_references', 0)
        if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 0:
            raise ValueError(f'{field}.{raw_key}.min_references must be a non-negative integer')
        result[raw_key] = SectionReferenceRule(allowed_types=allowed_types, min_references=minimum)
    return result


def _optional_section_key(value, field: str, sections: set[str]) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or value not in sections:
        raise ValueError(f'{field} must name a declared logical section')
    return value


def _knowledge_contracts(data, entity_types: tuple[str, ...]) -> dict[str, KnowledgeEvidenceContract]:
    raw_contracts = data.get('knowledge_evidence_contracts', {})
    if not isinstance(raw_contracts, dict):
        raise ValueError('knowledge_evidence_contracts must be an object')
    contracts: dict[str, KnowledgeEvidenceContract] = {}
    for raw_name, raw_contract in raw_contracts.items():
        if not isinstance(raw_name, str) or not raw_name.strip():
            raise ValueError('knowledge_evidence_contracts keys must be non-empty strings')
        name = raw_name.strip()
        if not isinstance(raw_contract, dict) or not raw_contract:
            raise ValueError(f'knowledge_evidence_contracts.{name} must be a non-empty object')
        include = _include_patterns(raw_contract.get('include'), f'knowledge_evidence_contracts.{name}.include')
        required = _sections(raw_contract.get('required_sections'), f'knowledge_evidence_contracts.{name}.required_sections')
        states = _sections(raw_contract.get('knowledge_state_sections', {}), f'knowledge_evidence_contracts.{name}.knowledge_state_sections', allow_empty=True)
        if set(required) & set(states):
            raise ValueError(f'knowledge_evidence_contracts.{name} logical section keys must be unique')
        rules = _reference_rules(raw_contract.get('reference_rules'), f'knowledge_evidence_contracts.{name}.reference_rules', set(required) | set(states), entity_types)
        contracts[name] = KnowledgeEvidenceContract(include, required, states, rules)
    return contracts


def _relationship_contracts(data, entity_types: tuple[str, ...]) -> dict[str, RelationshipMemoryContract]:
    raw_contracts = data.get('relationship_memory_contracts', {})
    if not isinstance(raw_contracts, dict):
        raise ValueError('relationship_memory_contracts must be an object')
    contracts: dict[str, RelationshipMemoryContract] = {}
    for raw_name, raw_contract in raw_contracts.items():
        if not isinstance(raw_name, str) or not raw_name.strip():
            raise ValueError('relationship_memory_contracts keys must be non-empty strings')
        name = raw_name.strip()
        if not isinstance(raw_contract, dict) or not raw_contract:
            raise ValueError(f'relationship_memory_contracts.{name} must be a non-empty object')
        include = _include_patterns(raw_contract.get('include'), f'relationship_memory_contracts.{name}.include')
        required = _sections(raw_contract.get('required_sections'), f'relationship_memory_contracts.{name}.required_sections')
        dimensions = _sections(raw_contract.get('dimension_sections', {}), f'relationship_memory_contracts.{name}.dimension_sections', allow_empty=True)
        if set(required) & set(dimensions):
            raise ValueError(f'relationship_memory_contracts.{name} logical section keys must be unique')
        all_sections = set(required) | set(dimensions)
        rules = _reference_rules(raw_contract.get('reference_rules'), f'relationship_memory_contracts.{name}.reference_rules', all_sections, entity_types)
        source = _optional_section_key(raw_contract.get('source_actor_section'), f'relationship_memory_contracts.{name}.source_actor_section', all_sections)
        target = _optional_section_key(raw_contract.get('target_actor_section'), f'relationship_memory_contracts.{name}.target_actor_section', all_sections)
        memory = _optional_section_key(raw_contract.get('memory_event_section'), f'relationship_memory_contracts.{name}.memory_event_section', all_sections)
        for role_name, key in (('source_actor_section', source), ('target_actor_section', target), ('memory_event_section', memory)):
            if key is not None and (key not in rules or rules[key].min_references < 1):
                raise ValueError(f'relationship_memory_contracts.{name}.{role_name} requires a reference rule with min_references >= 1')
        kind_section = _optional_section_key(raw_contract.get('kind_section'), f'relationship_memory_contracts.{name}.kind_section', all_sections)
        allowed_kinds = _strings(raw_contract.get('allowed_kinds', []), f'relationship_memory_contracts.{name}.allowed_kinds', allow_empty=kind_section is None)
        if kind_section is None and allowed_kinds:
            raise ValueError(f'relationship_memory_contracts.{name}.allowed_kinds requires kind_section')
        autonomy_section = _optional_section_key(raw_contract.get('autonomy_section'), f'relationship_memory_contracts.{name}.autonomy_section', all_sections)
        autonomy_states = _strings(raw_contract.get('allowed_autonomy_states', []), f'relationship_memory_contracts.{name}.allowed_autonomy_states', allow_empty=autonomy_section is None)
        if autonomy_section is None and autonomy_states:
            raise ValueError(f'relationship_memory_contracts.{name}.allowed_autonomy_states requires autonomy_section')
        allow_self = raw_contract.get('allow_self_relation', False)
        if not isinstance(allow_self, bool):
            raise ValueError(f'relationship_memory_contracts.{name}.allow_self_relation must be boolean')
        contracts[name] = RelationshipMemoryContract(include, required, dimensions, rules, source, target, memory, kind_section, allowed_kinds, autonomy_section, autonomy_states, allow_self)
    return contracts


def _chronology_contract(data, entity_types: tuple[str, ...]) -> ChronologyContract | None:
    raw = data.get('chronology_contract')
    if raw is None:
        return None
    if not isinstance(raw, dict) or not raw:
        raise ValueError('chronology_contract must be a non-empty object')
    event_types = _strings(raw.get('event_types'), 'chronology_contract.event_types')
    if any(item not in entity_types for item in event_types):
        raise ValueError('chronology_contract.event_types must be entity_types')
    before = _strings(raw.get('before_headings', []), 'chronology_contract.before_headings', allow_empty=True)
    after = _strings(raw.get('after_headings', []), 'chronology_contract.after_headings', allow_empty=True)
    causes = _strings(raw.get('causes_headings', []), 'chronology_contract.causes_headings', allow_empty=True)
    caused_by = _strings(raw.get('caused_by_headings', []), 'chronology_contract.caused_by_headings', allow_empty=True)
    if not any((before, after, causes, caused_by)):
        raise ValueError('chronology_contract must configure at least one relation heading')
    aliases = [item.casefold() for group in (before, after, causes, caused_by) for item in group]
    if len(aliases) != len(set(aliases)):
        raise ValueError('chronology_contract relation heading aliases must be unique')
    acyclic = raw.get('causality_acyclic', False)
    if not isinstance(acyclic, bool):
        raise ValueError('chronology_contract.causality_acyclic must be boolean')
    return ChronologyContract(event_types, before, after, causes, caused_by, acyclic)


def parse_advanced_contracts(data, entity_types: tuple[str, ...]) -> AdvancedContracts:
    return AdvancedContracts(
        knowledge_evidence_contracts=_knowledge_contracts(data, entity_types),
        relationship_memory_contracts=_relationship_contracts(data, entity_types),
        chronology_contract=_chronology_contract(data, entity_types),
    )
