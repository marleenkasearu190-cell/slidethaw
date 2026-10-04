# Installation

## Public dependencies

Use Python 3.10 or newer. The portable scripts use the standard library and Pillow:

```sh
python -m venv .venv
python -m pip install -r requirements.txt
```

Activate that virtual environment using your shell's standard activation command before
installing dependencies. The current build path additionally requires host-provided
Node.js, artifact-tool and the Presentations finalizer. See [compatibility](compatibility.md).
No API key is required by the supplied Python tools.

## Complete Skill installation

Clone [the repository](https://github.com/marleenkasearu190-cell/slidethaw) with an authorized
account while it is private, or extract the prepared source archive. From the project directory:

```sh
python tools/install_skill.py --destination ../slide-work/.agents/skills
```

This installs all scripts, templates and references, refuses an existing destination and
leaves the installed original untouched. Open `slide-work` in Codex and invoke
`$rebuild-ppt-image-compare`. Restart Codex if it does not discover the new Skill.
Avoid installing a second copy with the same name in another active discovery location.

Repository `.agents/skills` and user `~/.agents/skills` discovery are described in
[official skill documentation](https://learn.chatgpt.com/docs/build-skills).
The older local `.codex/skills` location is not the installation default for this project.
Copying into an isolated `.agents/skills` directory is exercised by the packaging tests;
fresh UI discovery must be checked in the receiving Codex session.

## Host runtime configuration

In a supported Codex session, call `load_workspace_dependencies` using the actual host
tool. It is **not a terminal command**. Use its returned executable/package paths and
the actual installed Presentations Skill directory for:

| Variable | Meaning |
| --- | --- |
| `REBUILD_SKILL_DIR` | Absolute path to this complete reconstruction Skill |
| `RUNTIME_PYTHON` | Host Python executable with Pillow |
| `RUNTIME_NODE` | Host Node.js executable |
| `RUNTIME_NODE_MODULES` | Host Node.js package directory |
| `RUNTIME_BIN_DIR` | Host binary directory returned by the loader |
| `SKILL_DIR` | Host Presentations Skill directory containing its finalizer |

Run `python tools/doctor.py --require build` after setting these process environment
variables. Set up the project `src/node_modules` link as described in the Skill's
implementation reference. Do not vendor the linked runtime into this repository.

The [synthetic example](../examples/synthetic-overview/README.md) documents the concrete
sequence for the supplied fixture. For a new image, let Codex inspect it and fill the
specifications before building; initialization alone is deliberately not a ready project.
