# Changelog

## 未发布：中文优先改造

- 中文默认首页与用户指南，保留英文入口和旧中文章节。
- 明确 `unit/build/wps/powerpoint` 的环境检查边界，不改变 CLI 或机器字段。
- 本地文档链接检查提前剪枝依赖、缓存与构建目录，增加中文路径和诊断分级回归测试。
- 便携 CI 补充 `main` push 触发；不运行 Office，不新增 Release、tag 或许可证。
- 既有英文示例与真实验收记录保留，不声明新增中文质量验证。

## v0.1.0-alpha.1 - 2026-10-04

Initial public prerelease; not a stable or general reconstruction-quality benchmark.

- Package the complete existing `rebuild-ppt-image-compare` Skill with metadata version 2.2.
- Preserve the default editable-only slide, optional comparison pair, frozen baseline,
  mixed editability, scoped edits and target-application acceptance.
- Add English/Chinese project documentation, dependency diagnosis, complete-folder
  installation, packaging tests and a synthetic integration example.
- Add distribution auditing and a metadata-only publication-copy sanitizer that
  preserves XML namespace bindings and leaves the original file unchanged.
- Retain the original deterministic tests and historical validation record separately
  from fresh repository validation.

- Publish the audited source, documentation and self-authored synthetic example.
- Keep host runtimes, credentials, font files and private user projects excluded.
- Leave the project-wide license unset at the maintainer's explicit request.

Known limits: a compatible host runtime is required; strict PowerPoint saved-copy
non-target pixel preservation failed; adapters and broader slide-quality benchmarks
are not validated. See [release notes](docs/releases/v0.1.0-alpha.1.md).

Skill metadata version 2.2 and repository release version are distinct.
