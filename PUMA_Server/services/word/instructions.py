from __future__ import annotations

import logging
import re
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from lxml import etree as ET  # type: ignore[reportMissingImports]

from services.word.package import write_zip_with_replacement
from services.word.text_rewrite import paragraph_text_nodes, replace_text_span
from services.word.xml_utils import NS


logger = logging.getLogger("uvicorn.error")

DEFAULT_TEMPLATE_INSTRUCTIONS = [
    "(delete sentences if not applicable)",
    "(delete sentence if not applicable)",
    "(delete chapter if not applicable)",
    "（如不需要删除这段）",
    "(如不需要删除这段)",
]

INSTRUCTION_SIDE_SPACE_CHARS = " \t\r\n\xa0\u3000"


@dataclass
class InstructionRemovalSummary:
    """记录模板提示语删除结果。"""

    instructions: list[str]
    replacements_applied: int
    changed_paragraphs: int


def instruction_removal_patterns(instructions: list[str]) -> list[re.Pattern[str]]:
    side_spaces = f"[{re.escape(INSTRUCTION_SIDE_SPACE_CHARS)}]*"
    return [
        re.compile(f"{side_spaces}{re.escape(instruction)}{side_spaces}")
        for instruction in instructions
        if instruction
    ]


def remove_instruction_patterns_in_paragraph(
    paragraph: ET.Element,
    patterns: list[re.Pattern[str]],
) -> int:
    applied = 0
    text_nodes = paragraph_text_nodes(paragraph)
    if not text_nodes:
        return applied

    for pattern in patterns:
        search_from = 0
        while True:
            combined_text = "".join(node.text or "" for node in text_nodes)
            match = pattern.search(combined_text, search_from)
            if match is None:
                break

            start, end = match.span()
            replace_text_span(text_nodes, start, end, "")
            applied += 1
            search_from = start

    return applied


def remove_template_instruction_text_in_xml(
    input_docm: Path,
    output_docm: Path,
    instructions: list[str] | None = None,
) -> InstructionRemovalSummary:
    """从正文 document.xml 中删除固定模板提示语。

    这里删除的是固定短语本身，不按黄色高亮判断，避免误删业务正文里的
    黄色强调内容。
    """
    target_instructions = instructions or DEFAULT_TEMPLATE_INSTRUCTIONS
    patterns = instruction_removal_patterns(target_instructions)

    with zipfile.ZipFile(input_docm, "r") as archive:
        document_xml = archive.read("word/document.xml")

    root = ET.fromstring(document_xml)
    replacements_applied = 0
    changed_paragraphs = 0
    for paragraph in root.findall(".//w:p", NS):
        applied = remove_instruction_patterns_in_paragraph(paragraph, patterns)
        if applied:
            replacements_applied += applied
            changed_paragraphs += 1

    if replacements_applied == 0:
        shutil.copy2(input_docm, output_docm)
    else:
        updated_document_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        write_zip_with_replacement(input_docm, output_docm, {"word/document.xml": updated_document_xml})

    return InstructionRemovalSummary(
        instructions=list(target_instructions),
        replacements_applied=replacements_applied,
        changed_paragraphs=changed_paragraphs,
    )


def remove_template_instruction_text(
    document_path: Path,
    instructions: list[str] | None = None,
) -> InstructionRemovalSummary:
    """删除报告正文中残留的模板维护提示语。

    作为固定收尾步骤使用：先完成规则删除和章节删除，再清理这些
    "(delete ... if not applicable)" / "（如不需要删除这段）" 提示。
    """
    with tempfile.TemporaryDirectory(prefix="puma_word_instruction_") as temp_dir:
        temp_path = Path(temp_dir) / document_path.name
        shutil.copy2(document_path, temp_path)

        output_path = Path(temp_dir) / f"{document_path.stem}_instructions{document_path.suffix}"
        summary = remove_template_instruction_text_in_xml(
            temp_path,
            output_path,
            instructions=instructions,
        )
        shutil.copy2(output_path, document_path)

    logger.info(
        "[TCD08] Removed template instruction text. replacements=%s paragraphs=%s",
        summary.replacements_applied,
        summary.changed_paragraphs,
    )
    return summary
