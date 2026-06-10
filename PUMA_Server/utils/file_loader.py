import json
import os
import re
from pathlib import Path

try:
    from PUMA_Server.utils.path_config import (
        TEMPLATES_DIR,
        DATA_SOURCE_DIR,
    )
except ImportError:  # pragma: no cover - fallback for direct script execution
    from utils.path_config import (
        TEMPLATES_DIR,
        DATA_SOURCE_DIR,
    )

# ============================================
#  通用 JSON 加载工具
# ============================================

def load_json(path: str | Path):
    """
    加载任意 JSON 文件（支持绝对路径和相对路径）
    """
    path = Path(path)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_template(filename: str):
    """
    加载 templates 下的 JSON 文件
    """
    path = TEMPLATES_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_data_source(filename: str):
    """
    加载 data_source 下的 JSON 文件
    """
    path = DATA_SOURCE_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================
#  JSON 写入工具
# ============================================

def write_json(path: str, data):
    """
    保存 JSON 文件（会自动创建目录）
    """
    path = Path(path)

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================
#  与 ProjectInfo 相关的业务逻辑工具（可保留）
# ============================================

def extract_root_paths(projectInfo: list):
    """
    从 projectInfo 结构中解析 Local Link / Public Link / SharePoint 根路径
    """

    root_paths = {
        "local": None,
        "public": None,
        "cloud": None,
    }

    for group in projectInfo:   # projectInfo 是一个二维数组
        for item in group:      # 每个 group 里是 label/value 对象
            label = item.get("label")
            value = item.get("value")

            if label == "Local Link":
                root_paths["local"] = value

            elif label == "Public Link":
                root_paths["public"] = value

            elif label == "SharePoint":
                root_paths["cloud"] = value

    return root_paths


def normalize_path_fragment(value: object, fallback: str = "") -> str:
    text = str(value or "").strip()
    if not text:
        return fallback

    text = re.sub(r"[\\/]+", "_", text)
    text = re.sub(r'[<>:"|?*]', "_", text)
    return text.strip(" .") or fallback


def replace_path_tokens(path_text: str, replacements: dict[str, object]) -> str:
    result = str(path_text or "")
    for token, replacement in replacements.items():
        if not token:
            continue
        result = result.replace(token, str(replacement))
    return result


def build_local_workspace_paths(
    projectInfo: list,
    calibration_id: str,
    *,
    create: bool = True,
) -> dict[str, Path]:
    """根据 Local Link 和 CalibrationID 生成本地工作区标准路径。"""
    root_paths = extract_root_paths(projectInfo)
    local_root = root_paths.get("local")
    if not local_root:
        raise ValueError("No Local Link configured in projectInfo")

    local_root_path = Path(local_root)
    application_root = local_root_path / "40.Application"
    vehicle_integration_root = application_root / "A.Vehicle_integration"
    algo_root = application_root / "B.Algo"
    calibration_token = normalize_path_fragment(calibration_id, fallback="CalibrationID")
    calibration_root = application_root / "C.Calibration" / calibration_token

    results_root = calibration_root / "03_Results"
    email_dir = results_root / "Customer_Approval_Email"
    official_release_root = calibration_root / "06_Official_Release"
    tcd08_report_dir = official_release_root / "TCD08_Report"

    calibration_folders = {
        "01_MDS": calibration_root / "01_MDS",
        "02_Parameter": calibration_root / "02_Parameter",
        "03_Results": results_root,
        "04_Internal_Release": calibration_root / "04_Internal_Release",
        "05_Test_Input": calibration_root / "05_Test_Input",
        "06_Official_Release": official_release_root,
    }

    if create:
        for folder in [
            application_root,
            vehicle_integration_root,
            algo_root,
            calibration_root,
            *calibration_folders.values(),
            email_dir,
            tcd08_report_dir,
        ]:
            folder.mkdir(parents=True, exist_ok=True)

    return {
        "local_root": local_root_path,
        "application_root": application_root,
        "vehicle_integration_root": vehicle_integration_root,
        "algo_root": algo_root,
        "calibration_root": calibration_root,
        "calibration_token": calibration_token,
        "results_root": results_root,
        "email_dir": email_dir,
        "official_release_root": official_release_root,
        "tcd08_report_dir": tcd08_report_dir,
        "calibration_folders": calibration_folders,
    }


def load_folder_mapping():
    """
    专门读取模板里的 FolderLinkMapping.json
    """
    path = TEMPLATES_DIR / "FolderLinkMapping.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
