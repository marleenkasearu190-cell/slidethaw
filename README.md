# SlideThaw

Turn slide images into editable PowerPoint with a Codex Skill and toolkit.

[中文说明](README.zh-CN.md)

SlideThaw reconstructs text and layout from slide screenshots or AI-generated slide
designs. The original image stays inside the working project for comparison. The default
deliverable is **one editable slide**. A two-slide original/reconstruction comparison is
available when requested.

**Environment:** the current builder needs a compatible Codex host with
`@oai/artifact-tool` and the host Presentations finalizer. These components are not
bundled or advertised as publicly installable npm dependencies. Final acceptance uses
actual WPS or PowerPoint on Windows. See [compatibility](docs/compatibility.md).

## Example

![Synthetic source on the left, actual WPS reconstruction on the right](examples/synthetic-overview/comparison-wps.png)

The [synthetic overview](examples/synthetic-overview/README.md) uses a self-authored HTML
reference rendered to a screenshot. It contains no research results, institution logos
or private user files. The example documents the actual build and desktop checks.
It is a small integration fixture, not a reconstruction-quality benchmark.
[Download the tested editable example](examples/synthetic-overview/overview_editable.pptx).
WPS acceptance passed. PowerPoint rendering passed for the final sanitized file;
its edit operations passed, but its saved copy failed the strict non-target pixel check.
See [the actual test record](docs/validation.md).

## Quick Start

Clone the repository (authorized access is required while it is private) or extract the
prepared source archive, install the public Python dependency, then copy the complete Skill
into a **new** repo-scoped Codex discovery directory:

```sh
git clone https://github.com/marleenkasearu190-cell/slidethaw.git
cd slidethaw
python -m pip install -r requirements.txt
python tools/install_skill.py --destination ../slide-work/.agents/skills
python tools/doctor.py
```

Open `slide-work` in Codex and invoke:

```text
Use $rebuild-ppt-image-compare to reconstruct this image as one editable slide.
Preserve the wording, numbers and layout. Complete real rendering and edit tests.
```

The Skill guides image interpretation, specification, building and review. The scripts
do not autonomously recognize and convert an arbitrary slide image. Follow
[installation](docs/installation.md) to resolve host runtime paths and renderer access.

## Editability

Titles, body text and simple layout shapes use native PowerPoint objects. Named semantic
groups support moving a module together. Complex artwork, logos and scientific plots
can remain original image crops with explicit exceptions.

The basic builder supports text, shapes, pictures and groups. Tables, charts,
connectors and mathematical objects require verified adapters. Unknown chart data
is preserved as an image. See [editability boundaries](docs/editability.md).

## How It Works

1. Preserve the source bytes and normalize image orientation without downsampling.
2. Confirm four specifications for the deck, content, scene and authorized edits.
3. Freeze the baseline, build native objects, then bind image names and native groups.
4. Finalize with the host toolchain and reopen the saved file in the target application.
5. Inspect actual renders and temporary edit copies before claiming acceptance.

Content bindings reject missing or altered text. A structural `PASS` is distinct from
rendering, visual review and editing acceptance. Diagnostic image differences do not
produce a fidelity percentage. See [architecture](docs/architecture.md).

## Validation And Limits

Run the public suites with Python and Pillow:

```sh
python -B -m unittest discover -s skills/rebuild-ppt-image-compare/tests -v
python -B -m unittest discover -s tests -v
python tools/check_links.py
```

[Validation record](docs/validation.md) distinguishes fresh tests from the preserved
v2.2 historical record. Office tests are local, separate from CI. No universal fidelity,
full editability, unattended conversion or platform compatibility claim is made.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md), [security guidance](SECURITY.md) and
[troubleshooting](docs/troubleshooting.md). The Skill invocation name remains
`rebuild-ppt-image-compare`, with metadata version 2.2. The proposed first repository
release is `v0.1.0-alpha.1`; a release will be linked only after it actually exists.

This independent project is maintained by [marleenkasearu190-cell](https://github.com/marleenkasearu190-cell).
The [repository](https://github.com/marleenkasearu190-cell/slidethaw) is currently private.
No public Release has been published. Public scope and code licensing remain subject
to the maintainer's confirmation before public release.
External components retain their own terms. See [third-party notices](THIRD_PARTY_NOTICES.md).
