from __future__ import annotations

import logging
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from lxml import etree as ET  # type: ignore[reportMissingImports]

from services.word.package import write_zip_with_replacement
from services.word.red_paragraphs import normalize_color, parse_red_colors
from services.word.xml_utils import NS, qn


logger = logging.getLogger("uvicorn.error")


@dataclass
class ColorReplacementSummary:
    """记录一次字体颜色替换的结果。"""

    source_colors: list[str]
    target_color: str
    changed_runs: int


def replace_font_colors_in_xml(
    input_docm: Path,
    output_docm: Path,
    source_colors: set[str],
    target_color: str,
) -> ColorReplacementSummary:
    """替换正文 document.xml 中指定字体颜色。

    只处理显式写在 run 属性里的 <w:color w:val="...">。
    模板里的红色可选文本就是这种形式；主题色、样式继承色不在这里改。
    """
    normalized_source_colors = {normalize_color(color) for color in source_colors if color}
    normalized_target_color = normalize_color(target_color)
    changed_runs = 0

    with zipfile.ZipFile(input_docm, "r") as archive:
        document_xml = archive.read("word/document.xml")

    root = ET.fromstring(document_xml)
    for color in root.findall(".//w:rPr/w:color", NS):
        current_color = normalize_color(color.get(qn("val")))
        if current_color not in normalized_source_colors:
            continue

        color.set(qn("val"), normalized_target_color)
        changed_runs += 1

    if changed_runs == 0:
        shutil.copy2(input_docm, output_docm)
    else:
        updated_document_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        write_zip_with_replacement(input_docm, output_docm, {"word/document.xml": updated_document_xml})

    return ColorReplacementSummary(
        source_colors=sorted(normalized_source_colors),
        target_color=normalized_target_color,
        changed_runs=changed_runs,
    )


def replace_red_font_with_black(
    document_path: Path,
    red_colors: set[str] | None = None,
    target_color: str = "000000",
) -> ColorReplacementSummary:
    """把正文里所有红色字体改成黑色。

    作为报告生成的固定收尾步骤使用：前面规则决定删哪些内容，
    最后这里把仍然保留下来的红色可选文本转成正式黑色文本。
    """
    colors = red_colors or parse_red_colors("FF0000,C00000")

    with tempfile.TemporaryDirectory(prefix="puma_word_color_") as temp_dir:
        temp_path = Path(temp_dir) / document_path.name
        shutil.copy2(document_path, temp_path)

        output_path = Path(temp_dir) / f"{document_path.stem}_black{document_path.suffix}"
        summary = replace_font_colors_in_xml(
            temp_path,
            output_path,
            source_colors=colors,
            target_color=target_color,
        )
        shutil.copy2(output_path, document_path)

    logger.info(
        "[TCD08] Replaced red font with black. changed_runs=%s target_color=%s",
        summary.changed_runs,
        summary.target_color,
    )
    return summary
