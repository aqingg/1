# TCD08 规则生成工具说明

本文档说明如何用 Excel 或固定格式文本生成 `tcd08_section_rules.json`。

## 推荐命令

在仓库根目录执行：

```powershell
python devtest/tcd08_rule_generator.py --validate PUMA_Server/config/tcd08_section_rules.json
```

生成 Excel 维护模板：

```powershell
python devtest/tcd08_rule_generator.py --init-excel PUMA_Server/config/tcd08_rules_template.xlsx
```

从 Excel 生成系统使用的 JSON：

```powershell
python devtest/tcd08_rule_generator.py --from-excel PUMA_Server/config/tcd08_rules_template.xlsx --output PUMA_Server/config/tcd08_section_rules.json
```

从固定格式文本生成系统使用的 JSON：

```powershell
python devtest/tcd08_rule_generator.py --from-text PUMA_Server/config/tcd08_rules.txt --output PUMA_Server/config/tcd08_section_rules.json
```

默认覆盖已有 JSON 前会创建时间戳备份。若只想替换 Excel 或文本中出现的顶层规则区，保留旧 JSON 中其他顶层内容，可增加 `--merge-existing`。

## Excel Sheet

Excel 工作簿支持以下 Sheet 名称。英文名和中文名都可以。

- `calibration_scope` / `章节删除`
- `condition_refs` / `条件定义`
- `red_paragraph_rules` / `段落删除`
- `red_paragraph_text_rules` / `文本改写`

列表字段建议用 `|` 分隔，例如 `FSR|IDF`、`2|3`。

## calibration_scope

用于生成 `calibration_scope.delete_when_missing`。

| 字段 | 含义 | 示例 |
| --- | --- | --- |
| `field_label` | 读取的表单字段，通常为 `Calibration Scope` | `Calibration Scope` |
| `required_any` | 任意一个存在即保留章节 | `FSR|IDF` |
| `sections` | 不满足时删除的章节 | `3.2` |
| `description` | 规则说明 | `Front algorithm` |

## condition_refs

用于生成可复用条件引用。

| 字段 | 含义 | 示例 |
| --- | --- | --- |
| `ref_name` | 条件引用名称 | `peripheral_has_ufs` |
| `field_label` | 读取的表单字段 | `Peripheral Sensor` |
| `operator` | 判断操作符 | `matches_any` |
| `value` | 判断值或正则 | `UFS[A-Z0-9]*` |
| `value_type` | `matches_all` 或列表值使用 `list` | `list` |
| `description` | 可选说明，不写入最终 JSON | `has UFS sensor` |

支持的 `operator`：

- `contains`
- `not_contains`
- `only_contains`
- `not_only_contains`
- `only_matches`
- `not_only_matches`
- `matches_any`
- `not_matches_any`
- `matches_all`

## red_paragraph_rules

用于生成红字段落组删除规则。

| 字段 | 含义 | 示例 |
| --- | --- | --- |
| `description` | 规则说明 | `Peripheral Sensor has no UFSx model` |
| `section` | 章节号 | `3.2` |
| `when_ref` | 条件引用，可用 `|` 写多个 | `peripheral_has_ufs|inertial_only_one_sma` |
| `when_json` | 可选内联条件 JSON | `{"Peripheral Sensor":{"matches_any":"UFS[A-Z0-9]*"}}` |
| `delete_groups` | 删除的红字段落组 | `2|3` |

通常优先使用 `when_ref`，只有临时规则才使用 `when_json`。

## red_paragraph_text_rules

用于生成红字段落内文字改写规则。多行使用同一个 `rule_id` 时，会合并为同一条规则的多个 `replacements`。

| 字段 | 含义 | 示例 |
| --- | --- | --- |
| `rule_id` | 改写规则 ID，用于合并多行替换 | `front_sensor_keep_ufs` |
| `description` | 规则说明 | `Section 3.2 front algorithm sensor description keeps UFS only` |
| `section` | 章节号 | `3.2` |
| `group` | 红字段落组序号 | `1` |
| `when_ref` | 条件引用，可用 `|` 写多个 | `peripheral_has_ufs|peripheral_no_pas` |
| `when_json` | 可选内联条件 JSON |  |
| `from` | 模板中的原始文本 | `central sensors, (and) UFS and PAS are used` |
| `to` | 目标文本，留空表示删除该文本 | `central sensors and UFS are used` |

## 固定格式文本

文本文件支持 section header 加 `key=value` 的格式：

```text
[condition_refs]
ref_name=peripheral_has_ufs; field_label=Peripheral Sensor; operator=matches_any; value=UFS[A-Z0-9]*

[red_paragraph_rules]
description=No UFS keeps central fallback; section=3.2; when_ref=peripheral_no_ufs; delete_groups=2|3

[red_paragraph_text_rules]
rule_id=front_keep_ufs; description=Keep UFS only; section=3.2; group=1; when_ref=peripheral_has_ufs|peripheral_no_pas; from=central sensors, (and) UFS and PAS are used; to=central sensors and UFS are used
```

也支持少量固定中文句式，例如：

```text
检查 Calibration Scope，如果不包含 FSR 或 IDF，则删除 3.2 Front algorithm。
检查 Peripheral Sensor，如果不包含 UFS，则删除 3.2 第 2、3 组红字段落。
```

中文句式解析能力是辅助入口，复杂规则仍建议使用 Excel 或 `key=value` 文本。

## 校验规则

生成器会在写入 JSON 前检查：

- 顶层结构是否为对象。
- 章节号是否类似 `3.2` 或 `3.2.1`。
- `delete_groups` 和 `group` 是否为数字。
- `when_ref` 是否能在 `condition_refs` 中找到。
- `when_json` 是否是合法 JSON 对象。
- `matches_all` 是否是列表。
- 文本改写规则的 `from` 是否为空。
