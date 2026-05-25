import getpass
import json
import logging
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.project import Project
from services.datamerge import (
    apply_project_info_overrides,
    fetch_single_project_details,
    fill_docx_by_placeholders,
)
from services.tcd08.rules import (
    red_paragraph_deletion_rules,
    red_paragraph_text_rewrite_rules,
    sections_to_delete_by_calibration_scope,
)
from services.word_sections import (
    replace_red_font_with_black,
    remove_template_instruction_text,
    remove_red_paragraph_groups,
    remove_word_sections,
    rewrite_red_paragraph_text,
    update_tocs_with_word,
)
from utils.file_loader import load_folder_mapping


logger = logging.getLogger("uvicorn.error")


def _merge_red_paragraph_deletions(red_deletions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按 section 合并 delete_groups，避免逐条删除造成组号重排。"""
    grouped_indexes: dict[str, set[int]] = defaultdict(set)
    grouped_rules: dict[str, list[str]] = defaultdict(list)

    for deletion in red_deletions:
        section = str(deletion.get("section", "")).strip()
        if not section:
            continue

        for group_index in deletion.get("delete_groups", []):
            try:
                grouped_indexes[section].add(int(group_index))
            except (TypeError, ValueError):
                continue

        description = str(deletion.get("description", "")).strip()
        if description:
            grouped_rules[section].append(description)

    merged: list[dict[str, Any]] = []
    for section, indexes in grouped_indexes.items():
        merged.append(
            {
                "section": section,
                "delete_groups": sorted(indexes),
                "matched_rules": grouped_rules.get(section, []),
            }
        )
    return merged

# 固定收尾处理开关：
# 如需临时保留模板里的删除提示语/红色字体，把对应值改为 False 即可。
REMOVE_TEMPLATE_INSTRUCTIONS_ENABLED = False
REPLACE_RED_FONT_WITH_BLACK_ENABLED = False


def _mapping_by_tag(tag_name: str) -> dict:
    """从 FolderLinkMapping.json 中找到指定 TagName 的配置项。"""
    for item in load_folder_mapping():
        if item.get("TagName") == tag_name:
            return item
    raise HTTPException(status_code=400, detail=f"No folder mapping found for {tag_name}")


def _mapping_base_path(item: dict, tag_name: str) -> Path:
    """读取某个 mapping 配置的 AbsolutePath，并确认路径存在。"""
    absolute_path = item.get("AbsolutePath") or ""
    if not absolute_path:
        raise HTTPException(status_code=400, detail=f"No AbsolutePath configured for {tag_name}")

    path = Path(absolute_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Configured path not found: {path}")
    return path


def _resolve_template_paths() -> list[Path]:
    """解析 TCD08 模板文件路径。"""
    item = _mapping_by_tag("ONETCD&TCD08_Template")
    base_path = _mapping_base_path(item, "ONETCD&TCD08_Template")
    file_keyword = (item.get("FileKeyWord") or "").strip()

    if file_keyword:
        if "/" in file_keyword or "\\" in file_keyword:
            raise HTTPException(
                status_code=400,
                detail="FileKeyWord must be a file name, not a path",
            )

        exact_file = base_path / file_keyword
        if not exact_file.is_file():
            raise HTTPException(
                status_code=404,
                detail=f"TCD08 template file not found: {exact_file}",
            )
        return [exact_file]

    if not base_path.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"TCD08 template mapping must point to a folder when FileKeyWord is empty: {base_path}",
        )

    template_paths = [
        path
        for path in sorted(base_path.iterdir())
        if path.is_file() and path.suffix.lower() in {".docx", ".docm"}
    ]
    if not template_paths:
        raise HTTPException(status_code=404, detail=f"No Word templates found in {base_path}")

    return template_paths


def _resolve_output_dir() -> Path:
    """解析 TCD08 报告输出目录，不存在则创建。"""
    item = _mapping_by_tag("ONETCD&TCD08_Report")
    absolute_path = item.get("AbsolutePath") or ""
    if not absolute_path:
        raise HTTPException(
            status_code=400,
            detail="No AbsolutePath configured for ONETCD&TCD08_Report",
        )

    output_dir = Path(absolute_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _load_project_info_from_db(project_id: Optional[int], db: Session) -> dict:
    """当前端没有直接传 project_info 时，从本地 DB 读取 projectInfo。"""
    if not project_id:
        return {}

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    try:
        return json.loads(project.projectInfo)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"projectInfo JSON decode error: {exc}",
        ) from exc


async def generate_tcd08_report(
    *,
    uuid: str,
    project_id: Optional[int],
    project_info: dict[str, Any],
    author: str,
    report_date: str,
    customer_release_email: str,
    db: Session,
) -> dict:
    """TCD08 报告生成主流程。

    这里负责“编排”：
    1. 获取 PMS profile。
    2. 合并 project_info。
    3. 计算章节删除、红字段落删除、段落内改写计划。
    4. 填充模板并调用 word_sections 执行 Word 修改。
    5. 组装与旧接口一致的返回结果。
    """
    request_start = time.perf_counter()
    logger.info("[TCD08] Start generating report. uuid=%s", uuid)
    profile_dict = await fetch_single_project_details(uuid)
    if not profile_dict:
        raise HTTPException(
            status_code=404,
            detail=f"无法检索到项目UUID '{uuid}' 的详细信息。",
        )

    resolved_project_info = project_info or _load_project_info_from_db(project_id, db)
    logger.info(
        "[TCD08] Project info loaded. source=%s project_id=%s",
        "request" if project_info else "database",
        project_id,
    )
    if resolved_project_info:
        profile_dict = apply_project_info_overrides(profile_dict, resolved_project_info)
        logger.info("[TCD08] Applied project info overrides to PMS profile.")

    profile_dict["author"] = (
        author
        or profile_dict.get("author")
        or profile_dict.get("project_leader")
        or getpass.getuser().upper()
    )
    profile_dict["report_date"] = (
        report_date or datetime.now().strftime("%Y.%m.%d")
    )
    profile_dict["customer_release_email"] = (
        customer_release_email or "N/A"
    )

    template_paths = _resolve_template_paths()
    output_dir = _resolve_output_dir()
    sections_to_delete = sections_to_delete_by_calibration_scope(resolved_project_info)
    red_paragraph_deletions = red_paragraph_deletion_rules(resolved_project_info, sections_to_delete)
    merged_red_paragraph_deletions = _merge_red_paragraph_deletions(red_paragraph_deletions)
    red_paragraph_text_rewrites = red_paragraph_text_rewrite_rules(resolved_project_info, sections_to_delete)
    logger.info(
        "[TCD08] Resolved %s template(s). output_dir=%s",
        len(template_paths),
        output_dir,
    )
    logger.info(
        "[TCD08] Section deletion plan from Calibration Scope: %s",
        sections_to_delete or "no sections to delete",
    )
    logger.info(
        "[TCD08] Red paragraph deletion plan: %s",
        merged_red_paragraph_deletions or "no red paragraph groups to delete",
    )
    logger.info(
        "[TCD08] Red paragraph text rewrite plan: %s",
        red_paragraph_text_rewrites or "no red paragraph text to rewrite",
    )

    saved_paths = []
    toc_update_paths: list[Path] = []
    section_delete_results = []
    red_paragraph_delete_results = []
    red_paragraph_text_rewrite_results = []
    instruction_removal_results = []
    color_replacement_results = []
    for index, template_path in enumerate(template_paths, start=1):
        template_start = time.perf_counter()
        logger.info(
            "[TCD08] (%s/%s) Filling template: %s",
            index,
            len(template_paths),
            template_path,
        )
        step_start = time.perf_counter()
        filled_stream = fill_docx_by_placeholders(profile_dict, template_path)
        logger.info(
            "[TCD08] (%s/%s) Placeholder filling took %.2fs.",
            index,
            len(template_paths),
            time.perf_counter() - step_start,
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"filled_{template_path.stem}_{timestamp}{template_path.suffix}"
        output_path = output_dir / output_name
        step_start = time.perf_counter()
        with open(output_path, "wb") as output_file:
            output_file.write(filled_stream.read())
        logger.info(
            "[TCD08] (%s/%s) Filled document saved in %.2fs: %s",
            index,
            len(template_paths),
            time.perf_counter() - step_start,
            output_path,
        )

        for text_rewrite in red_paragraph_text_rewrites:
            logger.info(
                "[TCD08] (%s/%s) Rewriting red paragraph text in section %s group %s.",
                index,
                len(template_paths),
                text_rewrite["section"],
                text_rewrite["group"],
            )
            step_start = time.perf_counter()
            rewrite_summary = rewrite_red_paragraph_text(
                output_path,
                section=text_rewrite["section"],
                group_index=text_rewrite["group"],
                replacements=[
                    (replacement["from"], replacement["to"])
                    for replacement in text_rewrite["replacements"]
                ],
                update_toc=False,
            )
            red_paragraph_text_rewrite_results.append(
                {
                    "file": str(output_path),
                    "section": rewrite_summary.section,
                    "group": rewrite_summary.group_index,
                    "rule": text_rewrite.get("description", ""),
                    "replacements_applied": rewrite_summary.replacements_applied,
                    "before": rewrite_summary.before_text,
                    "after": rewrite_summary.after_text,
                }
            )
            logger.info(
                "[TCD08] (%s/%s) Rewritten red paragraph text in %.2fs. replacements=%s",
                index,
                len(template_paths),
                time.perf_counter() - step_start,
                rewrite_summary.replacements_applied,
            )

        for red_deletion in merged_red_paragraph_deletions:
            logger.info(
                "[TCD08] (%s/%s) Removing red paragraph groups %s in section %s.",
                index,
                len(template_paths),
                red_deletion["delete_groups"],
                red_deletion["section"],
            )
            step_start = time.perf_counter()
            red_summary = remove_red_paragraph_groups(
                output_path,
                section=red_deletion["section"],
                selected_indexes=red_deletion["delete_groups"],
                update_toc=False,
            )
            red_paragraph_delete_results.append(
                {
                    "file": str(output_path),
                    "section": red_summary.section,
                    "requested_indexes": red_deletion.get("delete_groups", []),
                    "matched_rules": red_deletion.get("matched_rules", []),
                    "deleted_indexes": red_summary.deleted_indexes,
                    "remaining_red_groups": red_summary.remaining_red_groups,
                    "preview": red_summary.deleted_preview,
                }
            )
            logger.info(
                "[TCD08] (%s/%s) Removed red paragraph groups %s in %.2fs.",
                index,
                len(template_paths),
                red_summary.deleted_indexes,
                time.perf_counter() - step_start,
            )

        if sections_to_delete:
            logger.info(
                "[TCD08] (%s/%s) Removing sections after red paragraph processing: %s",
                index,
                len(template_paths),
                sections_to_delete,
            )
            step_start = time.perf_counter()
            deleted_sections = remove_word_sections(
                output_path,
                sections_to_delete,
                update_toc=False,
            )
            section_delete_results.extend(
                {
                    "file": str(output_path),
                    "section": result.removed_section,
                    "deleted_xml_nodes": result.deleted_xml_nodes,
                    "renumbered_paragraphs": result.typed_renumbered_paragraphs,
                    "preview": result.deleted_preview,
                }
                for result in deleted_sections
            )
            logger.info(
                "[TCD08] (%s/%s) Removed %s section(s) in %.2fs.",
                index,
                len(template_paths),
                len(deleted_sections),
                time.perf_counter() - step_start,
            )

        instruction_replacements_applied = 0
        if REMOVE_TEMPLATE_INSTRUCTIONS_ENABLED:
            logger.info(
                "[TCD08] (%s/%s) Removing template instruction text.",
                index,
                len(template_paths),
            )
            step_start = time.perf_counter()
            instruction_summary = remove_template_instruction_text(output_path)
            instruction_replacements_applied = instruction_summary.replacements_applied
            instruction_removal_results.append(
                {
                    "file": str(output_path),
                    "instructions": instruction_summary.instructions,
                    "replacements_applied": instruction_summary.replacements_applied,
                    "changed_paragraphs": instruction_summary.changed_paragraphs,
                }
            )
            logger.info(
                "[TCD08] (%s/%s) Removed template instruction text in %.2fs. replacements=%s",
                index,
                len(template_paths),
                time.perf_counter() - step_start,
                instruction_summary.replacements_applied,
            )
        else:
            logger.info(
                "[TCD08] (%s/%s) Template instruction removal disabled.",
                index,
                len(template_paths),
            )

        color_changed_runs = 0
        if REPLACE_RED_FONT_WITH_BLACK_ENABLED:
            logger.info(
                "[TCD08] (%s/%s) Replacing remaining red font with black.",
                index,
                len(template_paths),
            )
            step_start = time.perf_counter()
            color_summary = replace_red_font_with_black(output_path)
            color_changed_runs = color_summary.changed_runs
            color_replacement_results.append(
                {
                    "file": str(output_path),
                    "source_colors": color_summary.source_colors,
                    "target_color": color_summary.target_color,
                    "changed_runs": color_summary.changed_runs,
                }
            )
            logger.info(
                "[TCD08] (%s/%s) Replaced red font with black in %.2fs. changed_runs=%s",
                index,
                len(template_paths),
                time.perf_counter() - step_start,
                color_summary.changed_runs,
            )
        else:
            logger.info(
                "[TCD08] (%s/%s) Red-to-black font replacement disabled.",
                index,
                len(template_paths),
            )

        if (
            sections_to_delete
            or red_paragraph_deletions
            or red_paragraph_text_rewrites
            or instruction_replacements_applied
            or color_changed_runs
        ):
            logger.info(
                "[TCD08] (%s/%s) Queued document for batched Word TOC update.",
                index,
                len(template_paths),
            )
            toc_update_paths.append(output_path)

        saved_paths.append(str(output_path))
        logger.info(
            "[TCD08] (%s/%s) Template processing completed in %.2fs.",
            index,
            len(template_paths),
            time.perf_counter() - template_start,
        )

    if toc_update_paths:
        logger.info(
            "[TCD08] Updating Word TOC for %s document(s) in one Word session.",
            len(toc_update_paths),
        )
        step_start = time.perf_counter()
        update_tocs_with_word(toc_update_paths)
        logger.info(
            "[TCD08] Batched Word TOC update took %.2fs.",
            time.perf_counter() - step_start,
        )

    logger.info(
        "[TCD08] Report generation completed in %.2fs. saved_paths=%s",
        time.perf_counter() - request_start,
        saved_paths,
    )
    return {
        "status": "success",
        "message": "TCD08报告已成功生成并保存。",
        "template_paths": [str(path) for path in template_paths],
        "saved_paths": saved_paths,
        "section_deletions": section_delete_results,
        "red_paragraph_deletions": red_paragraph_delete_results,
        "red_paragraph_text_rewrites": red_paragraph_text_rewrite_results,
        "instruction_removals": instruction_removal_results,
        "color_replacements": color_replacement_results,
    }
