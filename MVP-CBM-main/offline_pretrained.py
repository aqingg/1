import os
import socket


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PRETRAINED_DIR = os.path.join(PROJECT_ROOT, "pretrained")
HF_HOME = os.path.join(PRETRAINED_DIR, "hf_home")
HF_HUB = os.path.join(HF_HOME, "hub")
TORCH_HOME = os.path.join(PRETRAINED_DIR, "torch_home")


BIOMEDCLIP_REPO_CACHE = os.path.join(
    HF_HUB,
    "models--microsoft--BiomedCLIP-PubMedBERT_256-vit_base_patch16_224",
)
TIMM_VIT_REPO_CACHE = os.path.join(
    HF_HUB,
    "models--timm--vit_base_patch16_224.augreg2_in21k_ft_in1k",
)


def configure_offline_environment():
    os.environ.setdefault("HF_HOME", HF_HOME)
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", HF_HUB)
    os.environ.setdefault("TORCH_HOME", TORCH_HOME)
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("DISABLE_TELEMETRY", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def _snapshot_dirs(repo_cache_dir):
    snapshots_dir = os.path.join(repo_cache_dir, "snapshots")
    if not os.path.isdir(snapshots_dir):
        return []
    return [
        os.path.join(snapshots_dir, name)
        for name in os.listdir(snapshots_dir)
        if os.path.isdir(os.path.join(snapshots_dir, name))
    ]


def _find_snapshot_with_files(repo_cache_dir, required_files, any_of_files=None):
    for snapshot_dir in _snapshot_dirs(repo_cache_dir):
        required_ok = all(
            os.path.isfile(os.path.join(snapshot_dir, filename))
            for filename in required_files
        )
        if not required_ok:
            continue
        if any_of_files:
            any_ok = any(
                os.path.isfile(os.path.join(snapshot_dir, filename))
                for filename in any_of_files
            )
            if not any_ok:
                continue
        return snapshot_dir
    return None


def _format_missing_cache_message(missing_items):
    lines = [
        "离线预训练模型缓存不完整，训练已停止。",
        "",
        "请先在有网机器运行：",
        "  python download_pretrained.py",
        "",
        "然后把整个 pretrained/ 文件夹复制到服务器。",
        "",
        "缺失内容：",
    ]
    lines.extend(f"  - {item}" for item in missing_items)
    lines.extend([
        "",
        "当前缓存路径：",
        f"  HF_HOME={os.environ.get('HF_HOME')}",
        f"  HUGGINGFACE_HUB_CACHE={os.environ.get('HUGGINGFACE_HUB_CACHE')}",
        f"  TORCH_HOME={os.environ.get('TORCH_HOME')}",
    ])
    return "\n".join(lines)


def require_train_mvpcbm_pretrained_cache():
    configure_offline_environment()

    missing = []
    biomed_snapshot = _find_snapshot_with_files(
        BIOMEDCLIP_REPO_CACHE,
        required_files=[
            "open_clip_config.json",
            "open_clip_pytorch_model.bin",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "tokenizer.json",
            "vocab.txt",
        ],
    )
    if biomed_snapshot is None:
        missing.append(
            "BiomedCLIP 完整快照："
            + os.path.join(
                BIOMEDCLIP_REPO_CACHE,
                "snapshots",
                "<revision>",
            )
            + "，需要 open_clip_config.json、open_clip_pytorch_model.bin 和 tokenizer 文件"
        )

    timm_snapshot = _find_snapshot_with_files(
        TIMM_VIT_REPO_CACHE,
        required_files=["config.json"],
        any_of_files=["model.safetensors", "pytorch_model.bin"],
    )
    if timm_snapshot is None:
        missing.append(
            "timm ViT 完整快照："
            + os.path.join(
                TIMM_VIT_REPO_CACHE,
                "snapshots",
                "<revision>",
            )
            + "，需要 config.json 以及 model.safetensors 或 pytorch_model.bin"
        )

    print("Offline pretrained cache:")
    print("  HF_HOME =", os.environ.get("HF_HOME"))
    print("  HUGGINGFACE_HUB_CACHE =", os.environ.get("HUGGINGFACE_HUB_CACHE"))
    print("  TORCH_HOME =", os.environ.get("TORCH_HOME"))
    print("  HF_HUB_OFFLINE =", os.environ.get("HF_HUB_OFFLINE"))
    print("  TRANSFORMERS_OFFLINE =", os.environ.get("TRANSFORMERS_OFFLINE"))
    if biomed_snapshot:
        print("  BiomedCLIP snapshot =", biomed_snapshot)
    if timm_snapshot:
        print("  timm ViT snapshot =", timm_snapshot)

    if missing:
        raise FileNotFoundError(_format_missing_cache_message(missing))


def block_network_access():
    if os.environ.get("MVP_CBM_ALLOW_NETWORK", "0") == "1":
        print("WARNING: MVP_CBM_ALLOW_NETWORK=1，网络阻断已关闭。")
        return
    if getattr(socket, "_mvp_cbm_network_blocked", False):
        return

    original_socket = socket.socket
    original_create_connection = socket.create_connection
    original_getaddrinfo = socket.getaddrinfo

    def _blocked_error(target):
        raise RuntimeError(
            "检测到代码试图访问网络，已被 MVP-CBM 离线保护拦截。\n"
            f"目标：{target}\n"
            "如果这是 HuggingFace/timm/open_clip 下载请求，请先运行 "
            "python download_pretrained.py 准备 pretrained/ 缓存。\n"
            "如确实需要联网调试，可设置 MVP_CBM_ALLOW_NETWORK=1。"
        )

    class OfflineSocket(original_socket):
        def connect(self, address):
            _blocked_error(address)

        def connect_ex(self, address):
            _blocked_error(address)

    def offline_create_connection(address, *args, **kwargs):
        _blocked_error(address)

    def offline_getaddrinfo(host, port, *args, **kwargs):
        host_text = str(host)
        if host_text in {"localhost", "127.0.0.1", "::1"}:
            return original_getaddrinfo(host, port, *args, **kwargs)
        _blocked_error((host, port))

    socket.socket = OfflineSocket
    socket.create_connection = offline_create_connection
    socket.getaddrinfo = offline_getaddrinfo
    socket._mvp_cbm_network_blocked = True
