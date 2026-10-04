# 架构说明

[中文首页](../README.md) | [编辑性边界](editability.md) | [验证记录](validation.md)

`skills/rebuild-ppt-image-compare/` 是完整的既有 v2.2 Skill；原有脚本、模板、调用名与元数据保留不变。
发布辅助工具放在 `tools/`，不是另一套重建引擎。

| 阶段 | 既有实现 |
| --- | --- |
| 隔离工作项目并保留原图 | `init_compare_project.py` |
| 跨文件规格校验 | `contracts.py`、`validate_specs.py` |
| 冻结内容基准 | `freeze_baseline.py` |
| 原始像素裁切与来源记录 | `crop_asset.py` |
| 基础原生构建 | `build_compare.mjs`，使用 artifact-tool |
| 图片命名绑定与原生分组后处理 | `bind_native.py` |
| 最终导出检查 | `finalize_compare.mjs`，使用宿主 finalizer |
| PPTX 包与内容检查 | `pptx_inspect.py`、`qa_compare_pptx.py` |
| 真实渲染与临时副本编辑 | `office_render.ps1` |
| 诊断差分 | `visual_diff.py` |

四份规格为 `deck_spec.json`、`content_manifest.json`、`scene_graph.json` 和 `edit_plan.json`。
冻结后内容清单保持不变；获准删除的范围沿冻结场景的子节点展开。替换内容写入 edit plan，而不是直接篡改基准。
这些文件、字段名与机器状态不因文档中文化而更名。

默认 `editable_only` 模式中，原图仅内部对照；`comparison` 模式先输出参考页，再输出可编辑页。
对象绑定与 QA 页码映射跟随模式，双页对照只能在用户要求时生成。

发布工具提供环境诊断、安全复制完整目录、文档链接检查与发布审计；它们单独测试，不改变 authoring engine。
示例准备脚本使用人工明确的场景与内容，不是任意图片识别引擎。
单元测试中的模拟回执只验证接受/拒绝规则，不能充当真实 Office 操作证据。
最终文件还须哈希匹配、真实渲染、视觉观察和编辑验收，不能只依靠 XML 或结构 `PASS`。
