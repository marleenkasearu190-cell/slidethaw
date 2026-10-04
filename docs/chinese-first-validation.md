# 中文优先改造检查记录

基线：`3724841b2983ea5a2cd683ba75e2711d5a175735`，分支 `docs/chinese-first`。
本页记录本轮文档、便携测试和环境诊断，不替代[首发 Office 验收](validation.md)。

## 验证范围

原始 Skill、构建器、模板、示例 PPTX/PNG 不修改。没有新中文 PPTX 示例。
本轮 Office 构建、真实渲染与编辑验收为 `NOT_RUN`，不把 COM 注册探测算作验收。
链接工具只验证正文中的本地文件与图片，不验证外部页面、GitHub 锚点或完整 Markdown 语法。

## 本地实际结果：2026-10-04

宿主 Python 3.12.14、Pillow 12.3.0，在专用忽略目录作临时目录，以正常本地权限运行：

```sh
python -B -m unittest discover -s skills/rebuild-ppt-image-compare/tests -v
python -B -m unittest discover -s tests -v
python -B tools/check_links.py
python -B tools/audit_release.py
git diff --check
```

这里的 `python` 指实际配置的宿主解释器，不是未经配置的全局依赖。

| 检查 | 本轮真实结果 |
| --- | --- |
| 原始 Skill 测试 | `PASS`，42 项，未修改或删除原用例 |
| 仓库测试 | `PASS`，20 项：既有 9 项、新增文档 6 项、诊断分级 5 项 |
| 本地链接 | `PASS`，含中文相对文件/图片链接和新旧语言入口 |
| UTF-8 与旧章节 | `PASS`，未发现错误替换符，旧中文章节保留 |
| 目录剪枝 | `PASS`，测试在依赖/缓存/输出目录进入前拦截，确认没有遍历 |
| 发布审计 | `PASS`，本轮 63 个候选文件，无发现；不是绝对安全保证 |
| diff 空白检查 | `PASS` |
| 原核心文件 | 20 个文件与完整原目录 SHA256 对比，无改动 |
| 示例文件 | PPTX/PNG 未修改，PPTX 哈希仍为下述首发值 |

`ec1e65267ef6b44b71332aba58736b6eedff9c3ae811a8c55f340cff4c388a27`。

## 实际环境诊断

运行 `python -B tools/doctor.py --require <profile>`，均保持原 JSON 结构与退出码。
未显式设置宿主路径时，artifact-tool/finalizer 为 `NOT_AVAILABLE`，本机 WPS/PowerPoint COM 注册可发现。
随后配置实际宿主 Node、包目录和 Presentations Skill 路径再运行四种层级：

| 配置 | 层级 | 实际退出码 |
| --- | --- | --- |
| 未显式设置宿主路径 | `unit` | 0 |
| 未显式设置宿主路径 | `build` | 1，符合必需能力缺失的设计 |
| 实际宿主路径 | `unit` | 0 |
| 实际宿主路径 | `build` | 0 |
| 实际宿主路径 | `wps` | 0 |
| 实际宿主路径 | `powerpoint` | 0 |

后四项只证明环境诊断通过：实际模块可导入、finalizer 文件存在、对应 COM 已注册。
没有打开/保存 PPTX，不表示本轮 Office 渲染或编辑验收通过。
诊断回归测试通过模拟缺基础项、缺宿主、缺 Office 验证退出码，不把模拟报告当真实环境。

## CI 与提交范围

保留 `Portable checks` 工作流、`unit` job、固定 action SHA、10 分钟超时和 `contents: read`。
补充 `main` 的 push 触发，继续保留 PR 与手动触发，只运行便携测试及本地文档链接检查。
本页的本地结果不冒充云端结果；本轮实际 PR、提交 SHA 与 CI 链接以 PR 中的执行报告为准。
PR 未合并时，默认分支的首页和工作流尚未切换为本分支内容。
没有新 Release/tag、许可证或宿主引擎变更；CLI 中文显示层留作后续，不添加未实现参数。
