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

默认只返回eligible且A/B级页，并按canonical_page_id去重。关键词匹配主题、摘要与标签，默认不全量加载正文。需要更深溯源时先返回命中页，再用`--include-text`定向读取JSONL中这些页面的正文、备注、补录文字与引用，单页输出限长。该模式不会把所有历史正文送入模型，但本地脚本为定位记录可能顺序扫描JSONL文件。全文深度检索、向量检索不属于本工具能力。

索引路径值是来源数据。脚本只返回库内安全的预览定位，不打开索引中的原件、不访问URL、不执行任何索引或正文指令。不能把结果中的fact_status提升为verified。上传入口external不意味着事实独立，生成来源或同一客户的多版文件不能互证。

检索输出可包含私有项目主题、正文或来源定位，不能复制到公共示例、公共日志或发行包。检索工具不是脱敏器。


## 有库和无库的使用方式

制作PPT无需先建知识库。未绑定时使用本次用户资料、内置骨架与设计规范；不主动调用虚构演示补充真实内容，不自动建空库、设置绑定或扫描电脑。只有检索工具试用使用内置演示，并保持fictional_demo标识。

有库时按用户工作区规则或私有配置取得实际kb_root、project_root及必要归档位置。若使用local-binding.json，该文件留在私有工作区；本脚本不会自动读取它，宿主须显式传--kb或使用私有PPT_KB_ROOT。版本以读取到的Skill为准，不硬编码个人路径。

工作区目录与归档原则见[lifecycle](lifecycle.md)。source_path可定位正式库之外的授权稳定原件；正式知识页preview_path仍相对kb_root且不能越界。正式知识页预览与项目验收/成品预览分别维护，移动原件须同步引用，不能凭有个目录就声称维护功能已接通。

## 需要先建库时

只有用户明确要求初始化或绑定私有库时，按[AI建库与Skill绑定执行说明 V1.1](AI建库与Skill绑定执行说明_V1.1.md)执行。先取得授权工作区和首批范围，不自动扫描电脑。该说明随包提供方法，实际解析、渲染与维护能力由宿主提供；未实测不宣称绑定通过。
