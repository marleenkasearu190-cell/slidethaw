# SlideThaw 维护约定

保留 `rebuild-ppt-image-compare` 调用名和 Skill 元数据版本 2.2。
保持既有 artifact-tool 构建器与宿主 Presentations finalizer；不得为文档或发布便利替换引擎。
默认一页可编辑输出，仅在用户要求时生成双页对照。
保留四份规格、冻结基准、精确内容绑定、授权修改范围、局部图像例外和真实目标应用验收。

根 `README.md` 是中文默认首页，`README.en.md` 是英文入口；保留 `README.zh-CN.md` 的旧地址与章节。
用户说明优先中文；CLI 参数、JSON 字段、机器状态和 Skill 元数据不随翻译更名。
相关改动运行两套 unittest 和 `python tools/check_links.py`。
结构测试、模拟回执或合成示例不能代表实际 Office 操作或重建质量验收；未执行项记为 `NOT_RUN`。
记录本轮检查时，不覆盖已有验收失败、限制与历史记录。

来源证据、桌面回执与个人路径保留在 `.release-private/`，不要提交。
只发布自制或明确获准的示例；不打包运行时、系统 Skill、字体、凭据。
维护者当前选择暂不设置项目许可证；不能自动变更许可、发布新版或扩大公开范围。
每次构建和测试使用独立输出目录。
