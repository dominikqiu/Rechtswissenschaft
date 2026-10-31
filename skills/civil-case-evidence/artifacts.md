# 案件台账约定（衍生版新增）

在私有案件目录保存 case.json、报告与合法保存的来源摘录。case.json 的最小顶层结构见 [模板](examples/case-template.json)。模板故意留空，不能视作可交付案件。

| 集合 | 每条记录必填字段 |
| --- | --- |
| facts | id, text, status (stated/disputed/unknown), locator |
| sources | id, kind (norm/case/literature/method), title, locator, version, verification (verified/unverified/failed), applicability (applicable/inapplicable/uncertain), applicability_reason |
| retrievals | id, query, tool, at, scope, outcome, source_ids 数组 |
| claims | id, direction, remedy, nature, decision (included/excluded/pending), decision_reason, relationship, issue_ids 数组 |
| issues | id, question, proposition, application, counterargument, conclusion, result (supported/not_supported/conditional/unresolved), fact_ids 数组, source_ids 数组；有条件或争议/未知事实时另填 conditions |

每个 issue 至少归属于一个 claim；排除候选也需一个 issue 说明依据。一个 issue 只表达一个规则命题与结论；复杂争点拆分，避免多个命题共用一组模糊来源。fact_ids 只链接本结论实质依赖的事实；source_ids 只链接实际用于支持该单元的来源。反对观点另设 issue 并回应；不适用来源可留在 sources 供比较，但不能冒充适用依据。

verified 来源另需 url_or_path、ISO 日期/时间 accessed_at、实际读取的 excerpt 和其 UTF-8 SHA-256 excerpt_sha256。哈希按保存的摘录逐字计算，不做隐式空白转换。历史法可标 applicable，适用理由必须说明过渡依据；完整规范时间字段及裁判/文献元数据见 knowledge.md。

review 包含 open_items 数组。reviewed 另需 source_support、temporal_scope、fact_fidelity、alternatives、remedy_consistency 五项非空审查说明，写明检查的 ID 与结果，不能填“已检查”敷衍。程序只能检查字段，不能判断说明是否可信。

provisional 允许缺少或未核验来源，但不允许断裂引用。reviewed 要求所有 issue 无 unresolved、所链接来源均 verified/applicable 且不能只有 method 来源，open_items 为空。已经明确界定条件和分支的 conditional 可以 reviewed；尚未解决的依据或事实核验问题必须进入 open_items 并保留 provisional。材料缺失本身可作为条件分支，但不得伪称已查明。

验证器不验证 URL、摘录与网页一致性、检索日志真实性、法律适用理由或结论正确性。将未发生的核验填成 verified 仍属错误；代码通过不是法律质量认证。数额计算、依赖传播与来源去重按工作流人工核对，本版本未实现自动法律推理引擎。
