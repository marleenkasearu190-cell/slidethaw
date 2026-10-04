# Editability Boundaries

| Visible content | Representation | Editing boundary |
| --- | --- | --- |
| Titles, body, numbers, labels | Native text | Exact wording bound to content manifest; real edit tests required |
| Frames and simple layout | Native shapes | Position, fill and outline editable |
| Semantic modules | Actual native groups | Group movement tested in a temporary copy |
| Complex art, logos, scientific plots | Original crop/image | Can move or resize; internal pixels are not native objects |
| Tables/charts with reliable source data | Requires a verified native adapter | Basic template does not implement them |
| Connectors | Requires verified native connection adapter | Endpoints, arrows and movement must be tested |
| Mathematical expressions | Verified native math or declared image/SVG exception | SVG scaling does not mean formula editability |

The Skill preserves source image dimensions and crops original pixels. It does not
regenerate logos, maps, experimental curves or scientific formulas. A visible text item
has one display carrier; hidden text cannot satisfy the content check.

Local changes use a recorded edit plan and frozen baseline. The tools protect textual
and structural invariants; deciding whether geometry changes exceed the user's request
still needs review against the before/after renders.

The release evidence gate requires the actual final-file hash, matching target software
receipt, visual observations and evidence paths. Hashes and XML cannot prove glyph
legibility, clipping, occlusion or mathematical correctness. Unperformed checks remain
`NOT_RUN`. Inapplicable checks use `NOT_APPLICABLE` with a reason.
