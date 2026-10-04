# Changelog

## v0.1.0-alpha.1 - 2026-10-04

Initial public prerelease; not a stable or general reconstruction-quality benchmark.

- Package the complete existing `rebuild-ppt-image-compare` Skill with metadata version 2.2.
- Preserve the default editable-only slide, optional comparison pair, frozen baseline,
  mixed editability, scoped edits and target-application acceptance.
- Add English/Chinese project documentation, dependency diagnosis, complete-folder
  installation, packaging tests and a synthetic integration example.
- Add distribution auditing and a metadata-only publication-copy sanitizer that
  preserves XML namespace bindings and leaves the original file unchanged.
- Retain the original deterministic tests and historical validation record separately
  from fresh repository validation.

- Publish the audited source, documentation and self-authored synthetic example.
- Keep host runtimes, credentials, font files and private user projects excluded.
- Leave the project-wide license unset at the maintainer's explicit request.

Known limits: a compatible host runtime is required; strict PowerPoint saved-copy
non-target pixel preservation failed; adapters and broader slide-quality benchmarks
are not validated. See [release notes](docs/releases/v0.1.0-alpha.1.md).

Skill metadata version 2.2 and repository release version are distinct.
