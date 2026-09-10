# Performance engineering

Optimize architecture before micro-optimizing Java syntax.

## Hot-path questions

For every tick/event/listener that may fire frequently:

- How many owners/levels/chunks/entities can execute it?
- What collections are traversed?
- What is the worst-case bound?
- What allocates each invocation?
- Does it load chunks, query large AABBs, search registries, serialize data, or send packets?
- Can work be event-driven, indexed, cached, amortized, or budgeted?

## Required boundedness

Queues/caches/propagation/retries must have a capacity, retirement/invalidation, or a proof that cardinality is inherently bounded.

Avoid whole-world scans and scanning all loaded chunks every tick. Prefer maintained indexes of active objects, chunk-local data, scheduled work queues, or event-driven membership.

## Measurement

Do not call code "optimized" from inspection alone. When performance is material, capture a repeatable workload and runtime evidence (timing/profiling/allocation/tick behavior) with the tools available to the repository/environment.
