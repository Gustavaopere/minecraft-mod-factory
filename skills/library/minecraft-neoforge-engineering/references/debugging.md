# Systematic debugging

Do not patch from the last line of a stack trace alone.

## Reproduce

Capture:

- exact action/command;
- environment and side;
- branch/HEAD;
- relevant mod/dependency versions;
- first meaningful exception/assertion;
- reproducibility and minimal conditions.

## Classify first causal layer

Typical layers: Gradle/dependency resolution, compilation, datagen/resources, registry/bootstrap, dedicated-server classloading, persistence/world load, networking, gameplay/state machine, rendering/client, optional integration.

## Hypothesize

A root-cause hypothesis must predict an observation that distinguishes it from alternatives. Run the smallest check that can falsify it.

## Fix and regress

After the patch, reproduce the original path, run focused tests, then adjacent regressions. Confirm a new error is not simply masking the old one. Add a regression test when a deterministic seam exists.
