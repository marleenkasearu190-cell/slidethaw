# SlideThaw

保留设计，还原可编辑的文字与结构。

[English](README.md)

SlideThaw 是将幻灯片截图和 AI 生成设计图重建为可编辑 PowerPoint 的 Codex Skill 与工具包。
默认每张图独立输出 **一页可编辑 PPTX**，原图留在内部工作目录供对照。
明确要求“双页对照”时，输出原图页和重建页。

**运行环境：**当前构建器依赖兼容 Codex 宿主提供的 `@oai/artifact-tool` 和
Presentations finalizer。本项目不包含这些运行时，也没有核实其公共 npm 安装渠道。
最终验收需要 Windows 上的真实 WPS 或 PowerPoint。详情见[兼容性说明](docs/compatibility.md)。

## 实际示例

![左侧为合成原图，右侧为真实 WPS 重建渲染](examples/synthetic-overview/comparison-wps.png)

[合成示例](examples/synthetic-overview/README.md)从自制 HTML 的截图开始重建，记录实际构建、
渲染和编辑检查。不包含真实科研结果、学校 Logo 或私人文件，也不作为批量还原质量基准。
[下载已验收的可编辑示例](examples/synthetic-overview/overview_editable.pptx)。
WPS 完整验收通过；最终脱敏副本的 PowerPoint 渲染通过，编辑操作也通过，但保存后的非目标像素严格检查失败。

## 快速开始

克隆仓库（私有阶段需要授权访问），或解压源码包后，在项目目录执行：

```sh
git clone https://github.com/marleenkasearu190-cell/slidethaw.git
cd slidethaw
python -m pip install -r requirements.txt
python tools/install_skill.py --destination ../slide-work/.agents/skills
python tools/doctor.py
```

在 Codex 打开 `slide-work`，调用：

```text
使用 $rebuild-ppt-image-compare 将这张图片还原为一页可编辑 PPTX。
保留原文、数字和布局，完成实际渲染与编辑验收。
```

完整目录安装脚本拒绝覆盖已有同名 Skill。宿主运行时的设置见[安装说明](docs/installation.md)。
识图、规格确认和视觉审阅由 Codex 配合工具完成，脚本本身不提供任意图片的自动识别转换。

## 编辑性边界

标题、正文、数字、简单框架使用原生文字和形状；语义分组支持整体移动。
复杂图片、Logo、科学图和复杂公式可以保留原尺寸裁切，并明确不可编辑例外。
基础构建器支持文字、形状、图片和分组；表格、图表、连接器和数学对象需增加经过验证的适配器。
不能从图形高度猜原始数据。详见[编辑性说明](docs/editability.md)。

## 内容保护与验收

四份规格分别记录页面、完整内容、对象结构和用户授权修改。冻结基准保护原文及对象归属，
修改范围通过 edit plan 表达。最终文件需要真实目标软件重新打开、渲染、对照检查及临时副本编辑测试。
结构 `PASS` 仅代表结构检查，像素差分仅用于诊断，不生成“还原率”。

```sh
python -B -m unittest discover -s skills/rebuild-ppt-image-compare/tests -v
python -B -m unittest discover -s tests -v
python tools/check_links.py
```

测试状态见[验证记录](docs/validation.md)，流程见[架构说明](docs/architecture.md)。
云端 CI 的结构测试与桌面 Office 验收分别记录。

## 维护与贡献

本项目由 [marleenkasearu190-cell](https://github.com/marleenkasearu190-cell) 独立维护，不代表 OpenAI、WPS 或 Microsoft 官方产品。
原调用名保留为 `rebuild-ppt-image-compare`，Skill 元数据版本为 2.2。
建议仓库首发版本为 `v0.1.0-alpha.1`，实际 Release 创建后再补链接。
[GitHub 仓库](https://github.com/marleenkasearu190-cell/slidethaw)目前为私有仓库，尚未发布公开 Release。
公开前需要维护者确认公开范围、代码与素材授权及许可证。

阅读[贡献指南](CONTRIBUTING.md)、[安全说明](SECURITY.md)、[排错说明](docs/troubleshooting.md)
和[第三方声明](THIRD_PARTY_NOTICES.md)。
