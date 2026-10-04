# Architecture

`skills/rebuild-ppt-image-compare/` is the complete existing v2.2 Skill. Its core
scripts and templates were copied intact. Packaging helpers live in `tools/`.

| Stage | Existing implementation |
| --- | --- |
| Isolated project and source preservation | `init_compare_project.py` |
| Cross-file specification validation | `contracts.py`, `validate_specs.py` |
| Content baseline lock | `freeze_baseline.py` |
| Original-pixel crop and provenance | `crop_asset.py` |
| Basic native authoring | `build_compare.mjs` using artifact-tool |
| Image-name binding and native group postprocessing | `bind_native.py` |
| Final export checks | `finalize_compare.mjs` using host finalizer |
| Package/content inspection | `pptx_inspect.py`, `qa_compare_pptx.py` |
| Actual render and temporary edit copy | `office_render.ps1` |
| Diagnostic differences | `visual_diff.py` |

The four specifications are `deck_spec.json`, `content_manifest.json`, `scene_graph.json`
and `edit_plan.json`. The content manifest stays intact after freezing. Approved removal
expands through descendants of the frozen scene. Authorized replacements are expressed
in the edit plan rather than changing the baseline.

The original image is internal in `editable_only` mode. `comparison` mode creates the
reference slide first and the editable slide second. The scene binding and QA page
mapping follow the selected mode.

New publishing helpers provide environment diagnosis, safe complete-folder installation
and Markdown-link checks. They are separately tested and do not change the authoring engine.
The synthetic fixture prep script is a manually specified example, not an image recognition
engine. Test receipts created inside unit fixtures exercise rejection/acceptance schemas
and are explicitly not evidence of actual Office operation.
