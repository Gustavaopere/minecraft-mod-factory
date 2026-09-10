# Blocks, items, entities, and block entities

Follow existing project conventions and exact 1.21.1 APIs.

## Blocks/items

Check registration, block item relationship, properties, loot/tags/recipes/models, interaction side, and state/property serialization.

## Block entities

Define creation, ticker side, persistence, synchronization, menu integration, and unload behavior. Avoid per-tick work when state transitions or scheduled ticks suffice.

## Entities

Define spawn/despawn, synced entity data, save/load, AI goals/brains, dimensions, tracking range/update rate, and server authority. Do not use client-only animation/render state as authoritative gameplay state.

## Components/data

When using item/entity data abstractions, verify mutation/copy/network behavior for the exact API generation; do not assume pre-1.21 patterns remain valid.
