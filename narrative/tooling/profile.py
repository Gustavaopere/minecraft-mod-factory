from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class NarrativeProfile:
    story_root: str
    dialogue_root: str
    entity_types: tuple[str, ...]
    editorial_state_prefixes: tuple[str, ...]
    editorial_state_headings: tuple[str, ...]
    dialogue_required_sections: dict[str, tuple[str, ...]]
    dialogue_entity_type: str


def _strings(value, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f'{field} must be a non-empty list of strings')
    return tuple(item.strip() for item in value)


def load_profile(path: str | Path) -> NarrativeProfile:
    data = json.loads(Path(path).read_text(encoding='utf-8'))
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
    return NarrativeProfile(
        story_root=story_root.strip(),
        dialogue_root=dialogue_root.strip(),
        entity_types=entity_types,
        editorial_state_prefixes=state_prefixes,
        editorial_state_headings=state_headings,
        dialogue_required_sections=sections,
        dialogue_entity_type=dialogue_entity_type,
    )
