# 可执行规格契约 2.2

初始化生成真实项目骨架，不附带假数据。`scripts/contracts.py` 是可执行字段与交叉引用验证器，仅依赖标准库。它不是通用 JSON Schema 引擎；扩展字段可用于当前构建器，但不能覆盖既有字段语义。新项目四份规格均 `schema_version: "2.2"`。旧 2.1 项目可按原双页模式继续验收，不自动改写旧项目。

## deck_spec.json

必需字段：`ready`、`mode`、`output_mode`、`slides`、`editable_slide`、`source`、`design_px:[W,H]`、`reference_bbox:[x,y,w,h]`、`output`、`template`、`runtime`。

|输出模式|slides|editable_slide / scene.slide|用途|
|---|---|---|---|
|`editable_only`（默认）|1|1|仅交付原生可编辑重建，原图内部保留|
|`comparison`（明确要求）|2|2|第 1 页完整原图，第 2 页重建|

不得混用页码；只有旧 2.1 规格省略 output_mode 时才按 comparison 解释。新 2.2 项目缺此字段即失败。

- `source.path`、素材路径与 `output` 为项目相对路径，不能逃出目录。原始路径只做溯源，不写回。
- `source.sha256` 是参考 PNG 的字节哈希，`size_px` 为 EXIF 转正后的原尺寸。`original_copy/original_sha256` 保留原附件原字节。
- `reference_bbox` 是原图等比映射到设计画布的位置，单页模式仍用于内部差分；非同宽高比采用明确留边，不分别拉伸 x/y。PPT 坐标可用 CSS px，但英寸/EMU 与预览像素分开记录；1 CSS px = 9525 EMU。
- `template.family_id`、`reference_match_verified:true` 必须针对当前参考图。复用时增加 `reuse_from`、相同的 `reuse_family_id` 和 `reuse_evidence`。
- `runtime.target_application` 为 `WPS` 或 `PowerPoint`；记录实际版本。其余环境用自己的真实渲染适配器，不能伪造本机 receipt。
- `style_tokens` 来自当前图，如 `font_zh`、`font_latin`、背景、边框、标题色、间距。没有强制所有页面用同一套蓝白色。

## scene_graph.json

`slide` 必须等于 `deck_spec.editable_slide`，默认 1。所有重建对象列入 `nodes`，源素材列入 `assets`。稳定 `id` 是语义标识，`name` 是最终 PPT cNvPr 的实际唯一名称，两者可一致。对象 ID 不以导出器随机序号代替。

节点示例（只是字段示意，坐标应从当前源图量取）：

```json
{"id":"result.card","name":"result.card","kind":"group","parent":null,"bbox":[80,200,500,240],"z":10,"native_group":true,"qa_region":true}
```

```json
{"id":"result.value","name":"result.value","kind":"text","parent":"result.card","bbox_local":[20,60,460,70],"z":12,"text_style":{"fontSize":46,"bold":true,"color":"#0746B5","autoFit":"none"}}
```

- `kind`: text / shape / picture / group / table / chart / formula / connector。
- `bbox` 是页面绝对设计像素，`bbox_local` 是相对父组件的位置，二者选一。父关系不能循环。`z` 是原始层叠顺序；本轮修复不得随机重排。
- 每个叶形状也需要记录。需要整体移动的模块 `native_group:true`，只是 scene 父关系不等于实际 PPT 分组。
- 图片有 `asset_id`，素材有 `id/path/sha256`，裁切额外记录 `crop_src_px`、原图哈希和图内文字归属。当前 QA 不允许 PPT 内二次裁图，先输出确认过的裁切文件。
- 连接器同时是 node，包含 `from/to` 节点 ID、`arrow`（forward/backward/both/none）、`binding_required`。`from/to` 对应 OOXML stCxn/endCxn；forward 表示末端箭头，不能只凭 API 的 head/tail 词面判断，必须看实际渲染。
- `qa_region:true` 用于关键区域对照。覆盖标题、指标、公式、科学图和底栏，不能只标空白背景。

## content_manifest.json

完整基准 `items`，每项包括 `id/text/confirmed/must_be_native/source/bindings`。

```json
{"id":"result.value","text":"micro RMSE：2.4820°C","confirmed":true,"must_be_native":true,"source":{"path":"source/reference.png","region_px":[300,200,400,80]},"bindings":[{"node_id":"result.value"}]}
```

表格 bindings 为 `{"node_id":"results.table","cell":[1,2]}`，行列从 0 开始。整段文本精确匹配对应载体；段落之间用 `\n`。只做 Unicode NFC，不删除空格，不合并正负号，不丢上标。分数/根号结构另做视觉和数学对象核查。

每个文本框或表格单元格绑定一个完整内容项；同一个内容确实出现两次可列两个 bindings，每处都要检查。未确认但必须原生的内容不能通过；确认不了的复杂图内字可以 `must_be_native:false`、`text:null`、`exception_reason` 并绑定 picture。不可把大量可读主要正文登记成图片例外逃避还原。

## edit_plan.json

首次解析完成后调用 `freeze_baseline.py`。它在 `qa/baseline/` 保存基准清单、初始对象图及哈希，再次执行仅验证，不覆盖。结构 QA 要求已有冻结记录。新的修订项目若沿用旧清单，应连同对应基准快照复制；修订中允许几何变化但不能改原始文字清单。批准的文字修正用 replacements 表达。

初始还原：`authorized:false`、`remove_components:[]`、`replacements:[]`、`protected_nodes:[]`。初始任务不需要为“忠实还原”重复索要确认。

授权删除例：

```json
{"schema_version":"2.2","authorized":true,"user_request":"删除数据产品模块，其他内容保留","remove_components":["products.section","products.edge"],"replacements":[],"protected_nodes":["header.logo","page.title"]}
```

删除按**基准** scene 递归展开到子对象，再过滤内容项 bindings。内容项所有 bindings 都被删除时，不再要求它出现在可编辑页；仍然留在原始清单及内部原图。双页模式原图页也保持不变。部分重复内容被删时，只要求剩下的载体。要删除的关联连接器必须包含在计划中，不能留下悬空端点。

冻结后不改 ID、name、kind 和 parent 内容归属；获准重排可改坐标，不能把子文字解挂到根来逃避模块删除。确需改变归属/结构时建立用户授权的新修订基准，保留旧基准用于比较。删除闭包始终从冻结快照计算，所有构建器和检查器使用同一规则。

`replacements:[{"content_id":"...","text":"获准的新原文","reason":"用户指出源数字有误"}]` 记录获准修正。基准 manifest 不修改。新对象图几何允许按获准范围调整，但应保存修改前的完整 spec 快照与非目标区域基准渲染；QA 的语义过滤不等于自动验证几何改动授权。

删除与文本修正只检查 editable_slide；不能把参考图或其他页的内容算入可编辑页检查。

## 测试计划和审阅记录

临时编辑测试示例：

```json
{"test_only":true,"operations":[{"op":"text","shape_name":"page.title","value":"相近长度测试标题"},{"op":"move","shape_name":"result.card","require_group":true,"dx_design_px":8,"dy_design_px":0}]}
```

可选 `table_cell`：增加 `shape_name/row/col/value`。图表数据/数学公式编辑必须另写并验证适配器，不支持时记录 NOT_RUN 并说明，不能伪报 PASS。

`qa/review.json` 的每项通过记录包含实际观察 `notes` 与 `evidence:[{"path":"qa/...png","sha256":"..."}]`。顶层 `pptx_sha256` 必须指向未被测试污染的最终文件。状态只能 PASS/FAIL/NOT_RUN/NOT_APPLICABLE。证据可来自编辑副本，但最终渲染 receipt 必须来自原规范文件。人/代理的观察仍必不可少，文件哈希不是视觉判断器。

单页模式 receipt 必须是 `slide_count:1` 且 outputs 仅 slide 1；双页为 2 且 outputs 各含 slide 1、2 一次。`reference_visual` 在单页模式仍必需，记录内部原图与实际重建渲染的对照，不可因没有原图幻灯片标为 NOT_APPLICABLE。
