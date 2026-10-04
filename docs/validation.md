# Validation Record

Fresh packaging validation date: **2026-10-04**. This record contains completed
checks for the prepared repository; the preserved [Skill v2.2 record](../skills/rebuild-ppt-image-compare/VALIDATION.md)
describes historical work and is not a claim that those tests were repeated here.

The original 42 deterministic tests passed with host Python 3.12.14 and Pillow 12.3.0.
Managed-sandbox attempts initially failed to write Python temporary files. The same
unmodified suite passed with normal local permissions in a dedicated scratch directory.

| Check | Actual result and scope |
| --- | --- |
| Existing deterministic suite | PASS, 42 tests |
| New packaging suite | PASS, 9 tests including installation, sample preparation, privacy rejection, metadata sanitization and namespace preservation |
| Native build and host finalizer | PASS, actual artifact-tool export, package/layout/font/import checks |
| Content and grouping | PASS, 8 exact native text carriers, one actual semantic group, one local image exception |
| WPS 14.0 render | PASS, actual single-slide PNG at 1280 x 720 |
| WPS edit/reopen | PASS, native title replacement and group movement by 8 design pixels |
| WPS non-target preservation | PASS, text/geometry unchanged and no changed pixels outside the permitted regions |
| WPS release evidence gate | PASS after final-file hash, real render receipt, visual review and edits were checked |
| PowerPoint 16.0 render | PASS, actual single-slide PNG at 1280 x 720 |
| PowerPoint edit/reopen operations | PASS, title replacement and group/child movement persisted |
| PowerPoint exact non-target pixel preservation | FAIL, pixels differ in unchanged text regions after saving the temporary copy; text and geometry still match |
| PowerPoint full acceptance | Not claimed because the strict non-target pixel check failed |

The preserved output PPTX SHA256 is
`ec1e65267ef6b44b71332aba58736b6eedff9c3ae811a8c55f340cff4c388a27`.
All actual before/after renders were opened and inspected. The WPS result is the complete
acceptance record for this fixture. PowerPoint's saved-copy rendering limitation remains
visible; no test was deleted or relaxed to present a full PASS.

The reference is self-authored HTML captured by Edge through Playwright, not an editable
source PowerPoint. The core adapter/templates were unchanged. The example's scene and
content were manually specified and checked. No reconstruction-time benchmark is reported.
Small text baseline differences between the HTML source and Office renders remain.
The original generated file contained exporter author fields. A separate publication copy
clears those fields without changing slide XML/media; the host finalizer was rerun and
the sanitized file was reopened/rendered in WPS. Its WPS render and edit renders have
the same SHA256 as the pre-sanitization renders. Original files and detailed evidence
remain in local ignored storage. The first metadata rewriter lost namespace declarations
used by date-field QName attributes, causing PowerPoint to refuse that intermediate copy.
The rewriter was fixed and a regression test added. The corrected final copy was actually
reopened/rendered in PowerPoint 16.0 successfully; its PNG hash matches the original
PowerPoint render. The broken intermediate copy is excluded from distribution.

Portable CI uses read-only permissions and verified upstream action SHAs. After the
repository became public, [manual CI run 37186807382](https://github.com/marleenkasearu190-cell/slidethaw/actions/runs/37186807382)
passed on Ubuntu with Python 3.12: 42 original tests, 9 packaging tests and local Markdown
links. The tested commit was `e8b4f189c9b0ce47c85c533e6716928eb108f436`; subsequent
publication records change documentation only. CI does not run desktop Office or
download the host runtime. Unperformed desktop or broader quality checks remain `NOT_RUN`.

Release-path/document auditing passed, including expanded PPTX metadata, notes,
relationships, embeddings and font checks. Gitleaks 8.30.1 scanned the isolated
distribution snapshot plus expanded PPTX XML and reported no leaks. No credentials,
personal source paths, runtime files, fonts or original user projects are distributed.
This combines automated checks with source/material review; it is not an absolute
security guarantee. The maintainer authorized public publication and explicitly chose
not to set a project-wide license for the source or sample.

Native tables/charts/math/connector adapters, dense Chinese slides, arbitrary-image
recognition, cross-platform desktop acceptance and large real-slide quality evaluation
are **NOT_RUN** in this release preparation. Synthetic fixtures do not establish those
capabilities or a fidelity percentage.
