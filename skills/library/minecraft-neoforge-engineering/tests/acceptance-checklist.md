# Skill acceptance checklist

## Packaging
- [ ] directory name matches `name`
- [ ] valid YAML frontmatter
- [ ] name/description/compatibility within Agent Skills limits
- [ ] SKILL.md below 500 lines
- [ ] local references resolve
- [ ] references remain focused and one level deep
- [ ] scripts are non-destructive and standard-library only

## Behavior
- [ ] exact-version API verification is mandatory
- [ ] repository bootstrap is mandatory for substantial existing-repo work
- [ ] planning does not block autonomous execution
- [ ] meaningful test-first development is preferred
- [ ] compile-only completion is prohibited
- [ ] dedicated-server classloading is explicitly checked
- [ ] server authority/network validation is explicit
- [ ] persistence/lifecycle/cleanup are explicit
- [ ] hot work must be bounded
- [ ] optional-mod classloading is isolated
- [ ] parallel branch contracts are not fabricated
- [ ] Git destructive actions require authorization
- [ ] completion claims require actual evidence

## Evaluation
- [ ] run baseline pressure scenarios without skill when possible
- [ ] run same scenarios with skill
- [ ] record failures/rationalizations
- [ ] revise minimal guidance that closes observed loopholes
- [ ] re-run after revisions
