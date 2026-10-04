# Compatibility

| Component | Distribution and role | Verified scope |
| --- | --- | --- |
| Python >=3.10 | Public runtime for scripts | Fresh tests passed on Python 3.12.14; other versions not freshly tested |
| Pillow >=10,<13 | Public Python dependency | Image normalization, cropping, pixel hashes and diagnostic differences |
| Node.js | Host runtime for ES modules | Actual artifact-tool import and example build recorded separately |
| `@oai/artifact-tool` | Supplied by a compatible Codex host | Basic adapter uses native text/shapes/pictures; public installation channel not verified |
| Presentations finalizer | Supplied by the host's system Skill | Required by the current Codex build profile; not redistributed |
| WPS for Windows | Separately licensed desktop application | Version 14.0 COM render, edits and complete example acceptance passed |
| PowerPoint for Windows | Separately licensed desktop application | Version 16.0 render/edit operations passed; strict saved-copy non-target pixel check failed |
| Playwright | Optional public development dependency | Used only to recapture the self-authored HTML reference image |
| GitHub CLI / Gitleaks | Maintainer publishing tools | Not runtime dependencies and not distributed with the Skill |
| Fonts | Provided by the operating system/user | No font files are bundled; substitute fonts may change layout |

Portable structure and unit tests can run without the build host or desktop Office.
The existing Office renderer uses Windows COM. macOS, Linux, LibreOffice, browser-only
PowerPoint and other hosts have not been validated for final acceptance by this project.
No alternative build engine is installed or substituted in this release preparation.

The basic adapter supports text, shape, picture and group. A schema or inspector accepting
tables, charts, connectors or formulas does not establish a complete builder or editing
adapter for those objects. See [editability](editability.md).
