# 安装说明

[中文首页](../README.md) | [English](../README.en.md) | [兼容性](compatibility.md)

## Python 依赖与虚拟环境

便携脚本使用 Python 3.10 或更新版本、标准库和 Pillow；首发实际测试环境为 Python 3.12.14、Pillow 12.3.0，其他版本未逐一验证。
在仓库根目录建立虚拟环境，并直接使用该环境的解释器，避免依赖被装进另一个 Python。

Windows PowerShell：

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe tools/doctor.py --require unit
```

macOS/Linux 的便携检查可使用：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/doctor.py --require unit
```

后者不是跨平台 Office 验收承诺；当前真实 Office 渲染器依赖 Windows COM。
上述 Python 工具不要求 API key。完整构建还需宿主提供的 Node.js、artifact-tool 与 Presentations finalizer。

## 安装完整 Skill

克隆[公开仓库](https://github.com/marleenkasearu190-cell/slidethaw)，或解压源码包。从仓库根目录执行：

```powershell
& .\.venv\Scripts\python.exe tools/install_skill.py --destination ../slide-work/.agents/skills
```

安装器复制全部脚本、模板和参考文件，拒绝已有目标及覆盖源目录，不改动原始 Skill。
不要只复制 `SKILL.md`。在 Codex 打开 `slide-work`，确认会话发现 `$rebuild-ppt-image-compare` 后调用。
未发现时重启会话；避免在多个活动发现位置安装同名副本。

仓库级 `.agents/skills` 和用户级 `~/.agents/skills` 的发现规则见[官方 Skill 文档](https://learn.chatgpt.com/docs/build-skills)。
本项目不默认安装到旧的 `.codex/skills` 位置。
打包测试验证完整目录复制，但接收端 Codex 的 UI 发现仍需在实际会话中确认。

## 宿主运行时配置

在支持该工具的 Codex 会话中，通过实际宿主工具调用 `load_workspace_dependencies`。
它不是终端命令，也不保证所有 Codex 会话都提供。若不可用，必须确认实际宿主组件及路径，不能用虚构路径或未经核实的 npm 包替代。
使用工具返回的可执行文件、包目录和已安装的 Presentations Skill 路径设置当前进程变量：

| 变量 | 含义 |
| --- | --- |
| `REBUILD_SKILL_DIR` | 完整重建 Skill 的绝对路径 |
| `RUNTIME_PYTHON` | 安装了 Pillow 的宿主 Python 可执行文件 |
| `RUNTIME_NODE` | 宿主 Node.js 可执行文件 |
| `RUNTIME_NODE_MODULES` | 宿主 Node.js 包目录 |
| `RUNTIME_BIN_DIR` | 宿主工具返回的二进制目录 |
| `SKILL_DIR` | 包含 finalizer 的宿主 Presentations Skill 目录，不是重建 Skill 目录 |

按[原实现参考](../skills/rebuild-ppt-image-compare/references/implementation-pattern.md)创建项目 `src/node_modules` 到宿主包目录的链接。
不要把链接指向的运行时复制进仓库。当前构建引擎不变，也不把宿主组件宣传为已验证的公共 npm 依赖。

## 环境检查分级与退出码

`doctor.py` 始终输出 JSON；默认 `--require unit`。退出 0 表示当前所选层级的必需项通过；否则退出 1。
报告会列出其他层级的检查，即使它们不是本次的必需项。

| 参数 | 影响退出码的必需项 |
| --- | --- |
| `--require unit` | 完整 Skill、Python、Pillow |
| `--require build` | 上述三项，加 artifact-tool 实际 ES module 导入、finalizer 文件存在 |
| `--require wps` | `build` 条件，加 WPS COM 类型注册可发现 |
| `--require powerpoint` | `build` 条件，加 PowerPoint COM 类型注册可发现 |

`unit` 可以在缺少宿主组件或 Office 时通过，此时报告中的相关项可能为 `NOT_AVAILABLE`。
`build` 不调用 finalizer 构建；`wps/powerpoint` 只探测 COM 注册，不打开 PPTX。
所有分级均为环境诊断，不是转换、渲染、视觉审阅或编辑验收。当前 CLI 没有 `--lang` 或 `--format` 参数。

配置真实宿主路径后，在 Windows PowerShell 中按目标执行：

```powershell
& .\.venv\Scripts\python.exe tools/doctor.py --require build
& .\.venv\Scripts\python.exe tools/doctor.py --require wps
# 使用 PowerPoint 时选择下一条；不要求两款软件同时存在。
& .\.venv\Scripts\python.exe tools/doctor.py --require powerpoint
```

实际重建步骤见[合成示例](../examples/synthetic-overview/README.md)。新图片需要先检查图像、确认四份规格，再构建。
仅初始化目录不会得到可交付的项目；最终仍需实际目标软件重新打开、渲染、审阅和编辑测试。
