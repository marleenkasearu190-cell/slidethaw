# 兼容性说明

[中文首页](../README.md) | [安装说明](installation.md) | [验证记录](validation.md)

| 组件 | 来源与用途 | 已验证范围 |
| --- | --- | --- |
| Python >=3.10 | 脚本的公共运行时 | 首发实际测试 Python 3.12.14；未逐一重测其他版本 |
| Pillow >=10,<13 | 公共 Python 依赖 | 图像规范化、裁切、像素哈希与诊断差分 |
| Node.js | 宿主 ES module 运行时 | 实际 artifact-tool 导入与示例构建另见验证记录 |
| `@oai/artifact-tool` | 兼容 Codex 宿主提供 | 基础适配器原生文字、形状与图片；公共安装渠道未验证 |
| Presentations finalizer | 宿主系统 Skill 提供 | 当前构建路径必需；不随项目分发 |
| Windows WPS | 单独许可的桌面应用 | 14.0 COM 渲染、编辑和示例完整验收通过 |
| Windows PowerPoint | 单独许可的桌面应用 | 16.0 渲染和编辑操作通过；保存副本的非目标像素严格检查失败 |
| Playwright | 可选公共开发依赖 | 仅用于重新截图自制 HTML 参考图 |
| GitHub CLI / Gitleaks | 维护者发布工具 | 不是运行依赖，不随 Skill 分发 |
| 字体 | 系统或用户提供 | 不附带字体文件；字体替换可能改变布局 |

结构检查和单元测试可不依赖构建宿主或桌面 Office。既有公共 CI 已在 Ubuntu、Python 3.12 上通过便携测试，但不运行 Office。
当前 Office 渲染器使用 Windows COM；macOS、Linux、LibreOffice、浏览器版 PowerPoint 和其他宿主的最终桌面验收均未验证。
本次中文化不替换构建引擎，也不重跑既有 Office 验收。

`doctor.py --require unit` 检查基础依赖；`build` 增加模块导入与 finalizer 文件存在；`wps/powerpoint` 再增加对应 COM 注册探测。
这些层级的退出 0 不是实际渲染或编辑通过，见[安装说明](installation.md)。

基础适配器支持文字、形状、图片和分组。规格或检查器接受表格、图表、连接器、公式，不代表已有完整构建与编辑适配器。
见[编辑性边界](editability.md)。历史结果、失败项和本轮便携检查分别记录，不能互相替代。
