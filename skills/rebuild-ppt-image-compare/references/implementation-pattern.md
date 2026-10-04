# 本机适配与脚本

## 当前 Codex 配置

调用工作区依赖加载器，使用返回的 Node、Python、node_modules 和工具目录，不沿用旧机器路径，不硬编码插件版本。Python 工具依赖标准库；裁图/像素检查/差分额外需要 Pillow，当前 bundled Python 已有。不要为缺 jsonschema 安装一套全局环境，本包使用自带的可执行契约校验。

存在当前 Presentations Skill 时，读取其 `SKILL.md` 和要求的 implementation/API/finalization 参考。使用它规定的 artifact-tool，引擎限制不由本包放宽。运行其 operation marker 后再执行第一条 PPT 构建命令。

仅在不提供该工具链的其他环境：先检查实际可用的 PptxGenJS 或 Office 自动化能力，选单个已验证适配器，记录版本。不能凭此条绕过当前环境的构建规则。迁移与安装新工具不属于一张截图的默认操作。

## 基础构建器

把 `templates/build_compare.mjs` 复制到项目 `src/`，把这里的 `REBUILD_SKILL_DIR` 设为本 Skill 的实际路径；`RUNTIME_PYTHON` 使用加载器返回路径。在 `src/` 建立指向当前 bundled Node packages 的 `node_modules` junction/link，使用实际 Node 执行：

```text
<Node> <项目>/src/build_compare.mjs <项目>
```

先经 `validate_specs`，再输出 `tmp/candidate.pptx` 和经过名称/分组处理的 `tmp/bound.pptx`。均拒绝覆盖。这两个是草稿，不是已验收文件。源图与 assets 是已识别素材，不能用提示词替代 blob。

支持 text/shape/picture/group 的最小核心。依 scene 的 `z` 顺序放置；text 的 `text_style` 用当前 API 的 CSS px 字号/边距/对齐设置，不误当 point。遇到其他类型显式报错，由 Codex 读取当前 API 编写此页所需适配器。原生表格/图表/连接器的扩展属于正常还原工作，不需要问用户是否准许“继续写代码”。

`bind_native.py` 只在新副本中处理 spec.editable_slide（默认第 1 页）。图片先使用明确 alt 标记；本机某些 exporter 会丢 alt，此时按“嵌入图片像素哈希＋目标坐标”唯一匹配后写稳定名称，存在歧义即报错，不能按图片序号猜。原生分组按 scene parent 构建，不移动叶对象、不修改图片、不改变文字。分组要求子对象在原 z 顺序连续，否则报错避免改变层叠。它不是任意 PPTX 导入修复器，不支持把已有复杂 master/animation 结构随意复制进另一文件。

对于已有原生组或已绑定名称的自定义构建器，不重复调用分组后处理。最终对象类型、父组和位置必须由 QA 确认。不要因为某个构建器不支持 group 就只在 JSON 里标记分组。

## Finalizer

基础模板故意只写草稿。可复制本包 `templates/finalize_compare.mjs`，核对当前 Presentations 的 finalization 文档后使用。设置其实际 SKILL_DIR 和加载器返回的全部 RUNTIME_NODE、RUNTIME_PYTHON、RUNTIME_NODE_MODULES、RUNTIME_BIN_DIR。用 `tmp/bound.pptx` 作为 candidate，在 `output/` 写一个新最终文件。`explicitTotalSlideCount` 取 spec.slides；仍需保留的原生表格/图表声明绑定 spec.editable_slide，不写死第 2 页。字体策略来自当前参考/真实用户指定，不编造来源。保留 package integrity、layout 和 import 验证报告到内部目录。

若某个工具重写了 shape 名称/分组/字体，修复适配器，不改 manifest 来顺从错误成品。最终导出可能重写文件，必须重新跑内容绑定检查，再获取最终文件的真实目标软件渲染。

## 渲染与编辑

`office_render.ps1` 参数：`-Pptx` 最终文件，`-Project` 项目，`-Out` 新建的 qa/ 或 tmp/ 子目录，`-Application WPS|PowerPoint`。不改执行环境的全局策略；用当前 PowerShell 的文件调用方式执行。

脚本按设计像素和 spec.slides 导出，默认只渲染 1 页，记录软件版本/时间/输入与输出哈希。编辑测试也只定位 spec.editable_slide。它不调用 Quit、不终止已有 Office 进程，只关闭本次打开的 presentation。若 COM 功能不可用，保留 FAIL 证据，必要时用已授权 GUI 导出并记录真实操作，不伪造脚本成功。没有目标应用时交付说明“未完成该端验收”，不假称兼容。

带 `-EditPlan` 时先复制至新的临时目录，在副本内调用实际 Office 文本/移动/表格接口，保存再重新打开、导出。receipt 中的 PASS 只表示已执行记录的操作，不代表连接关系与排版自动验收；仍需看编辑前后图。

编辑测试只用相近长度文字和小范围移动，避免把任意超长输入造成的溢出当作还原失败。对于没有流程、表格、图表的封面，相应项可不适用，不为过测试而添加无关对象。

## 旧项目迁移

2.1 的双页项目保持原样可读。要把旧内容改成单页，新建修订项目，沿用原内容与素材，将输出映射设为 editable_only / slides:1 / editable_slide:1 / scene.slide:1，重新构建、冻结与验收；不覆盖旧双页 PPT，也不沿用旧两页渲染 receipt。基础模板原生生成一页，不先构建双页再删除。

不在旧目录重跑 init。新建修订项目，复制原图、真实素材与必要构建代码。旧 `deck_spec.json` 不含逐项绑定，不能机械改 `schema_version` 就声称升级完成；需要从实际源图和 PPT 补齐清单与 scene。保留旧交付供对照。

## 自检

```text
<Python> -B -m unittest discover -s <Skill>/tests -v
```

这些回归测试验证确定性检查的正反例，不是实际科研页面的还原质量评测。发布时另记真实软件烟测和未覆盖项目。
