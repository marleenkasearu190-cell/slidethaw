# Contributing

Report reproducible bugs in Issues or propose a focused pull request. Include the
environment, failing command, expected/actual behavior and a synthetic or authorized
sample. Remove credentials, private paths, unpublished data and unlicensed materials.

Keep the single-slide default, exact content protection, scoped edits and truthful mixed
editability. Preserve the existing builder unless an explicit architecture change is
discussed. Add tests for regressions in bindings, permissions, page mappings or evidence
checks. Do not lower acceptance requirements to make tests pass.

```sh
python -m pip install -r requirements.txt
python -B -m unittest discover -s skills/rebuild-ppt-image-compare/tests -v
python -B -m unittest discover -s tests -v
python tools/check_links.py
```

CI exercises portable tests. Host-dependent builds and actual Office acceptance need
separate evidence. Mark untested capabilities accurately. Any sample needs its own source,
rights and editing-boundary explanation.

The maintainer has explicitly chosen not to set a project-wide license at this time.
Bug reports are welcome. Agree on applicable contribution terms with the maintainer
before submitting code for inclusion; no project-wide open-source license is implied.
