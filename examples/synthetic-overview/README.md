# Synthetic Overview

This is a **self-authored synthetic integration example**. Its HTML reference is captured
as a PNG before reconstruction. No hidden editable source deck is used. The manually
specified scene and content represent this fixture only; `prepare_example.py` does not
recognize arbitrary images.

Source: [HTML](source.html), [raster input](source.png). The page contains only synthetic
text/layout and a self-authored raster pattern. Code and sample rights await the
maintainer's final public-license confirmation. No institutional, research or outside
image assets are included.

![Source and actual WPS render](comparison-wps.png)

[Editable PPTX](overview_editable.pptx), [WPS render](render-wps.png),
[PowerPoint render](render-powerpoint.png),
[temporary WPS edit render](edit-wps.png).
The distributed PPTX is the metadata-sanitized publication copy. Its slide content is
unchanged and its actual WPS render matches the earlier accepted render.

## Reproduce

Use the host configuration in [installation](../../docs/installation.md), including
`REBUILD_SKILL_DIR`, `SKILL_DIR` and the five runtime variables required by the templates.
In the compatible Codex host:

```sh
python examples/synthetic-overview/prepare_example.py --project-root scratch --name overview
python skills/rebuild-ppt-image-compare/scripts/validate_specs.py scratch/overview
```

Create `scratch/overview/src/node_modules` as a link to the host package directory.
Follow the installed Presentations Skill's operation marker rules before authoring,
then invoke the unchanged builders with the resolved host Node executable:

```powershell
& $env:RUNTIME_NODE scratch/overview/src/build_compare.mjs scratch/overview
& $env:RUNTIME_NODE scratch/overview/src/finalize_compare.mjs scratch/overview
& $env:RUNTIME_PYTHON skills/rebuild-ppt-image-compare/scripts/qa_compare_pptx.py scratch/overview/output/overview_editable.pptx --project scratch/overview
```

On Windows, render and edit the temporary copy with the existing script:

```powershell
& ./skills/rebuild-ppt-image-compare/scripts/office_render.ps1 -Pptx scratch/overview/output/overview_editable.pptx -Project scratch/overview -Out qa/wps-render -Application WPS
& ./skills/rebuild-ppt-image-compare/scripts/office_render.ps1 -Pptx scratch/overview/output/overview_editable.pptx -Project scratch/overview -Out qa/wps-edit -Application WPS -EditPlan scratch/overview/qa/edit-test-plan.json
```

Use `-Application PowerPoint` with separate output directories to test that application.
Generate diagnostic differences, actually inspect the evidence and complete
`qa/review.json` before running the Skill's `--release` acceptance gate.
The init command rejects an existing project directory. Use a new revision name for repairs.

## Scope

Eight text carriers, a frame, a horizontal rule and a native semantic group are editable.
The checkerboard is an original-pixel image crop; its internal pixels are not native.
The edit test replaces the title with similar-length text and moves the group 8 design
pixels to the right. Tables, connectors, chart data and native equations are not present.

Recapturing the HTML optionally needs Playwright and Chromium (or an installed supported
browser selected through `SLIDETHAW_BROWSER_CHANNEL`). A ready raster input is included,
so ordinary reproduction does not need Playwright. No paid generation API is used.

Actual results and approved output links are recorded after local acceptance in
[validation](../../docs/validation.md). No elapsed-time benchmark or fidelity percentage
is reported. Human/agent work includes inspecting the raster, specifying the scene and
reviewing actual renders. Minor baseline differences between HTML and Office are expected.
