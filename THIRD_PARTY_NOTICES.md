# 第三方声明与素材来源

重建 Skill 来自用户完整的既有 v2.2 实现，原目录未发现源代码许可证。
维护者已授权公开，并明确选择暂不设置项目级许可证；Skill 或合成示例均未被赋予 MIT、Apache-2.0 等项目级开源许可。
原 Skill 元数据与验证记录保留不变；发布辅助工具、文档及明确声明的自制示例是在打包任务中编写的。
本次文档中文化不改变这些授权选择。

| 外部组件 | 来源与条款 | 是否包含在项目中 |
| --- | --- | --- |
| Pillow | [官方项目与许可证](https://github.com/python-pillow/Pillow/blob/main/LICENSE) | 仅声明依赖 |
| Playwright | [官方项目](https://github.com/microsoft/playwright)，Apache-2.0 | 可选截图脚本导入；不打包库或浏览器 |
| Codex / artifact-tool / Presentations | 宿主提供的 OpenAI 组件，各自适用其条款 | 不打包运行时或系统 Skill 文件 |
| WPS / Microsoft PowerPoint | 单独许可的桌面应用 | 不包含二进制 |
| Arial 及其他字体 | 系统/供应商许可 | 仅引用字体名称，不附带或嵌入字体 |
| GitHub Actions | 上游 action 仓库，各自适用其许可证 | 仅工作流引用 |

自制 HTML 及其栅格输出没有外部 Logo、照片、未公开研究或外部数据。生成的 PPTX 保留该合成图片的局部裁切。
项目不包含第三方示例幻灯片或用户既有演示文稿。

本项目独立维护，未获 OpenAI、Microsoft、WPS 或 GitHub 的官方背书。
