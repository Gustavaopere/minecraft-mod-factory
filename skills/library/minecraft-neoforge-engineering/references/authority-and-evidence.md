# Authority and evidence

## Source ranking

For behavior implemented by the current build, use this priority:

1. repository-local instructions and code for project-specific behavior;
2. resolved source/JAR of the exact dependency version;
3. official version-matched documentation;
4. official version-matched examples;
5. maintainer issue/discussion material;
6. secondary community sources.

A newer generic doc can be wrong for 1.21.1. An older tutorial can explain a concept but cannot prove a signature.

## Confirmed vs inferred

Label material conclusions mentally as one of:

- confirmed from repository/source/docs/runtime evidence;
- inferred from confirmed facts;
- hypothesis to test;
- unknown/unverified.

Do not promote inference to fact in completion reports.

## Negative evidence

"Search found nothing" is not proof that an API or integration does not exist. Broaden source search, inspect dependency artifacts, and check alternate naming before concluding absence.
