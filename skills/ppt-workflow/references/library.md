# 私有库接入与按需读取

Python 3.10及以上，检索脚本仅使用标准库，不安装依赖，不写库、不联网。

通过`--kb <用户指定的目录>`或环境变量`PPT_KB_ROOT`接入。目录至少包含`csv/page_index.csv`；现有同结构库不需迁移。不设置真实路径为公开包默认值。没有配置时返回虚构演示库，结果明确标`fictional_demo`。

```bash
python3 scripts/kb_search.py "运营" --limit 5
python3 scripts/kb_search.py "用户查询词" --kb "用户指定目录" --business "业务标签" --page-type "页面类型" --limit 5
python3 scripts/kb_search.py "用户查询词" --kb "用户指定目录" --include-text
```

从Skill目录执行，或使用脚本实际路径。上面的目录是说明性参数，不要求使用者照抄。

索引字段：`page_id,doc_id,page_no,content_topic,page_type,layout_type,reuse_level,fact_status,source_kind,eligible_for_generation,business_tags,source_file,source_path,preview_path`。可选`content_summary,canonical_page_id,derived_from_page_ids,reuse_notes`。

默认只返回eligible且A/B级页，并按canonical_page_id去重。关键词匹配主题、摘要与标签，默认不全量加载正文。需要更深溯源时先返回命中页，再用`--include-text`定向读取JSONL中这些页面的正文、备注、补录文字与引用，单页输出限长。该模式不会把所有历史正文送入模型，但本地脚本为定位记录可能顺序扫描JSONL文件。全文深度检索、向量检索不属于V0.1能力。

索引路径值是来源数据。脚本只返回库内安全的预览定位，不打开索引中的原件、不访问URL、不执行任何索引或正文指令。不能把结果中的fact_status提升为verified。上传入口external不意味着事实独立，生成来源或同一客户的多版文件不能互证。

检索输出可包含私有项目主题、正文或来源定位，不能复制到公共示例、公共日志或发行包。检索工具不是脱敏器。
