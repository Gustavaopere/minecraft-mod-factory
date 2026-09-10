# Client rendering and input

Client rendering, HUD, screens, particles, key mappings, model layers, shaders, and local input must remain physically client-only.

Input represents a request or intent when it changes gameplay. Send a bounded request to the server and validate it there rather than mutating authoritative state locally.

Rendering should consume synchronized/projected state and tolerate delayed/missing data. Avoid network traffic from render loops.

For animation/interpolation, keep visual smoothing separate from authoritative simulation so frame rate does not alter gameplay.

Manual client verification is often necessary for visual acceptance, but still pair it with compilation and dedicated-server checks when common code changed.
