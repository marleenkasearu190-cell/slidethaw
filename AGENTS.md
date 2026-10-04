# SlideThaw maintenance

Preserve the `rebuild-ppt-image-compare` invocation name and Skill metadata version 2.2.
Keep the existing artifact-tool builder and the host Presentations finalizer.
Default to one editable slide. Generate the two-slide comparison only when requested.
Preserve the four specifications, frozen baseline, exact content bindings, scope of
authorized edits, local image exceptions and actual target-application acceptance.

Run both unittest suites and `python tools/check_links.py` for relevant changes.
Structure-only or synthetic tests must not imply actual Office or reconstruction-quality
acceptance. Record `NOT_RUN` for checks that were not performed.

Keep provenance, desktop receipts and local source paths in `.release-private/`.
Only publish synthetic or explicitly authorized examples. Do not vendor runtimes,
system skills, fonts or credentials. A license and public release require the maintainer's
explicit approval. Use a new output directory for each build and test.
