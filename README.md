# SlideThaw｜把幻灯片图片还原成可编辑 PPT

[English](README.en.md) | [安装说明](docs/installation.md) | [实际示例](examples/synthetic-overview/README.md) | [v0.1.0-alpha.1 预发布](https://github.com/marleenkasearu190-cell/slidethaw/releases/tag/v0.1.0-alpha.1)

SlideThaw 是将幻灯片截图和 AI 生成设计图重建为可编辑 PowerPoint 的 Codex Skill 与工具包。
默认每张图输出 **一页可编辑 PPTX**，原图保留在内部工作目录供对照；明确要求双页对照时，才输出原图页和重建页。
文字、数字和简单布局尽量使用原生对象，复杂图像保留局部素材，并明确编辑性边界。

**环境要求：**当前构建器需要兼容 Codex 宿主提供的 `@oai/artifact-tool` 和 Presentations finalizer。
本项目不包含这些组件，也未验证其公共 npm 安装渠道。最终验收需要 Windows 上的真实 WPS 或 PowerPoint。
安装 Python 依赖或通过 `unit` 环境检查，不等于已经具备完整转换环境。详见[兼容性说明](docs/compatibility.md)。

## 实际示例

![左侧为自制合成原图，右侧为真实 WPS 重建渲染](examples/synthetic-overview/comparison-wps.png)

[合成示例](examples/synthetic-overview/README.md)从自制 HTML 截图开始，由人工明确场景和内容规格，记录实际构建、渲染与编辑检查。
素材没有科研结果、机构 Logo 或私人文件；现有示例仍为英文，不是中文密集页面或批量还原质量基准。
[下载已测试的可编辑示例](examples/synthetic-overview/overview_editable.pptx)。

既有验收中，WPS 完整验收通过；PowerPoint 的最终脱敏文件渲染和编辑操作通过，但保存后的非目标像素严格检查失败。
本次文档中文化不重建示例，也不把历史结果说成新测试。见[真实验证记录](docs/validation.md)。

## 快速开始

在 Windows PowerShell 中克隆仓库、建立虚拟环境，并始终使用该环境的解释器：

```powershell
git clone https://github.com/marleenkasearu190-cell/slidethaw.git
cd slidethaw
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe tools/doctor.py --require unit
& .\.venv\Scripts\python.exe tools/install_skill.py --destination ../slide-work/.agents/skills
```

安装脚本复制完整 Skill，拒绝覆盖已有目标。打开 `slide-work` 的 Codex 会话，确认已发现 Skill 后调用：

```text
使用 $rebuild-ppt-image-compare 将这张图片还原为一页可编辑 PPTX。
保留原文、数字和布局，完成实际渲染与编辑验收。
```

识图、规格确认和视觉审阅由 Codex 配合工具完成，脚本本身不是任意图片的无人值守识别转换器。
宿主路径配置、其他平台的安装命令和 Skill 发现规则见[安装说明](docs/installation.md)。
`load_workspace_dependencies` 是部分宿主提供的工具，不是终端命令，也不保证在所有 Codex 会话中可用。

## 环境检查分级

`doctor.py` 默认使用 `--require unit`，输出 JSON。分级只决定哪些检查影响退出码，不代表实际构建或验收：

| 参数 | 必须满足 | 不代表什么 |
| --- | --- | --- |
| `--require unit` | 完整 Skill、Python 和 Pillow | 不要求宿主构建组件或 Office；它们显示 `NOT_AVAILABLE` 时仍可能退出 0 |
| `--require build` | `unit` 条件，加 artifact-tool 实际导入与宿主 finalizer 文件存在 | 不代表已构建、导出或渲染 PPTX |
| `--require wps` | `build` 条件，加 WPS COM 注册可发现 | 不代表 WPS 渲染、编辑或完整验收通过 |
| `--require powerpoint` | `build` 条件，加 PowerPoint COM 注册可发现 | 不代表 PowerPoint 渲染、编辑或完整验收通过 |

完成实际宿主配置后，再按所用软件执行 `--require build` 和 `--require wps` 或 `--require powerpoint`。
不要仅凭 COM 注册或结构 `PASS` 宣称兼容性。

## 编辑性与工作流程

标题、正文、数字和简单框架使用原生文字、形状；语义分组支持整体移动。
复杂图片、Logo、科学图和复杂公式可保留原始像素裁切。它们能移动、缩放，不意味着内部内容可原生编辑。
基础构建器支持文字、形状、图片和分组；表格、图表、连接器和数学对象需要经过验证的适配器。
不能通过曲线或柱高猜测原始数据。见[编辑性说明](docs/editability.md)。

| 请求 | 输出和保护约定 |
| --- | --- |
| 默认忠实重建 | 一页可编辑输出，原图内部对照，保留文字、数字和布局 |
| 混合编辑性 | 原生对象与明确声明的局部图像例外共存 |
| 指定范围修改 | 用 edit plan 记录授权，保护冻结基准与非目标内容 |
| 明确要求双页对照 | 原图在第一页，重建在第二页 |

流程保留四份规格：页面、完整内容、对象结构和授权修改。冻结基准后构建、绑定、导出，再用目标软件重新打开、真实渲染、审阅和编辑临时副本。
内容绑定拒绝漏字、改字；结构检查不能代替视觉与编辑验收。像素差分只用于诊断，不生成“还原率”。见[架构说明](docs/architecture.md)。

## 测试与已知限制

在上述虚拟环境中运行便携测试与文档检查：

```powershell
& .\.venv\Scripts\python.exe -B -m unittest discover -s skills/rebuild-ppt-image-compare/tests -v
& .\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
& .\.venv\Scripts\python.exe tools/check_links.py
```

[验证记录](docs/validation.md)分别记录首发的 42 项原始测试、9 项打包测试及本次改造检查。
CI 不运行桌面 Office，不下载宿主运行时。链接检查覆盖 Markdown 正文中的本地文件和图片链接，不验证 GitHub 锚点、外部网页或完整 Markdown 语法。
未经执行的能力如实标为 `NOT_RUN`，不宣称通用还原率、全部原生编辑、无人值守转换或跨平台桌面兼容性。

## 维护与贡献

原 Skill 调用名仍为 `rebuild-ppt-image-compare`，元数据版本仍为 2.2；仓库首发版本为 `v0.1.0-alpha.1`。
见[首发中文说明](docs/releases/v0.1.0-alpha.1.zh-CN.md)和保留的[英文版本说明](docs/releases/v0.1.0-alpha.1.md)。
旧入口 [README.zh-CN.md](README.zh-CN.md)继续保留。

阅读[贡献指南](CONTRIBUTING.md)、[安全说明](SECURITY.md)、[排错说明](docs/troubleshooting.md)和[第三方声明](THIRD_PARTY_NOTICES.md)。
本项目由 [marleenkasearu190-cell](https://github.com/marleenkasearu190-cell) 独立维护，不是 OpenAI、Microsoft、WPS 或 GitHub 的官方产品。
维护者选择暂不设置项目许可证；仓库公开不代表已授予 MIT、Apache-2.0 等项目级开源许可。外部组件仍适用其各自条款。
