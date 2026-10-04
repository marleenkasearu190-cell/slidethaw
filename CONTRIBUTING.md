# 贡献指南

[中文首页](README.md) | [安装说明](docs/installation.md) | [安全说明](SECURITY.md)

欢迎通过 Issue 报告可复现问题，或提出范围明确的 PR。说明环境、失败命令、预期与实际行为，并提供自制或获准的示例。
删除凭据、私人路径、未公开数据和未经授权素材；不要上传机密幻灯片或字体文件。

保持默认单页、精确内容保护、指定范围修改与如实声明的混合编辑性。
未经明确架构讨论，不替换既有构建器。绑定、权限、页码映射和证据门回归应有测试。
不能为通过测试而降低验收标准。

先按安装说明建立虚拟环境。在 Windows PowerShell 中运行：

```powershell
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -B -m unittest discover -s skills/rebuild-ppt-image-compare/tests -v
& .\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
& .\.venv\Scripts\python.exe tools/check_links.py
```

CI 只运行便携测试和本地文档链接检查。宿主构建、真实 Office 渲染与编辑验收需要独立证据；没执行的项记为 `NOT_RUN`。
每个示例必须说明来源、素材权利和编辑性边界，不把自制小示例推广为通用能力。

中文默认文档位于 `README.md` 和用户指南；英文入口保留在 `README.en.md`。
修改导航时维护两个入口及旧 `README.zh-CN.md`，不要翻译 CLI 参数或机器字段。
链接检查只覆盖正文中的本地文件/图片，不验证锚点和外部站点，提交前仍需人工审阅。

维护者明确选择暂不设置项目级许可证。欢迎问题报告；提交拟纳入项目的代码前，请先与维护者确认适用贡献条款。
仓库公开不表示自动授予项目级开源许可。
