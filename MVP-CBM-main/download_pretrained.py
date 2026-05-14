import os
import time
from contextlib import contextmanager


try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


ROOT = os.path.dirname(os.path.abspath(__file__))
PRETRAINED_DIR = os.path.join(ROOT, "pretrained")
HF_HOME = os.path.join(PRETRAINED_DIR, "hf_home")
HF_HUB = os.path.join(HF_HOME, "hub")
TORCH_HOME = os.path.join(PRETRAINED_DIR, "torch_home")

os.environ["HF_HOME"] = HF_HOME
os.environ["HUGGINGFACE_HUB_CACHE"] = HF_HUB
os.environ["TORCH_HOME"] = TORCH_HOME


def format_seconds(seconds):
    seconds = int(seconds)
    hours, rem = divmod(seconds, 3600)
    minutes, sec = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m {sec}s"
    if minutes:
        return f"{minutes}m {sec}s"
    return f"{sec}s"


@contextmanager
def step_timer(name):
    start = time.time()
    print(f"\n开始：{name}")
    try:
        yield
    finally:
        elapsed = time.time() - start
        print(f"完成：{name}，耗时 {format_seconds(elapsed)}")


def run_step(progress, name, func, optional=False):
    start_all = progress.start_time if progress is not None else None
    try:
        with step_timer(name):
            func()
    except Exception as exc:
        if optional:
            print(f"可选步骤失败，已跳过：{name}")
            print(repr(exc))
        else:
            print(f"必要步骤失败：{name}")
            raise
    finally:
        if progress is not None:
            progress.update(1)
            elapsed_all = time.time() - start_all
            avg = elapsed_all / max(progress.n, 1)
            remaining = avg * (progress.total - progress.n)
            progress.set_postfix({
                "已用": format_seconds(elapsed_all),
                "预计剩余": format_seconds(remaining),
            })


def download_hf_snapshot(repo_id):
    from huggingface_hub import snapshot_download

    return snapshot_download(
        repo_id=repo_id,
        cache_dir=HF_HUB,
        resume_download=True,
    )


def main():
    from open_clip import create_model_from_pretrained, get_tokenizer
    import timm

    os.makedirs(HF_HUB, exist_ok=True)
    os.makedirs(TORCH_HOME, exist_ok=True)
    os.makedirs(os.path.join(TORCH_HOME, "hub", "checkpoints"), exist_ok=True)

    steps = [
        (
            "下载 BiomedCLIP 完整 HuggingFace 仓库快照",
            lambda: download_hf_snapshot(
                "microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"
            ),
            False,
        ),
        (
            "验证 BiomedCLIP 主模型和 open_clip 配置可加载",
            lambda: create_model_from_pretrained(
                "hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"
            ),
            False,
        ),
        (
            "验证 BiomedCLIP tokenizer 文件可加载",
            lambda: get_tokenizer(
                "hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"
            ),
            False,
        ),
        (
            "下载 train_mvpcbm.py / infer.py 使用的 timm ViT 仓库快照",
            lambda: download_hf_snapshot(
                "timm/vit_base_patch16_224.augreg2_in21k_ft_in1k"
            ),
            False,
        ),
        (
            "验证 train_mvpcbm.py / infer.py 使用的 timm ViT 可加载",
            lambda: timm.create_model("vit_base_patch16_224", pretrained=True),
            False,
        ),
        (
            "可选：下载 train_blackbox.py 默认 ResNet50",
            lambda: timm.create_model("resnet50.a1_in1k", pretrained=True),
            True,
        ),
        (
            "可选：下载 blackbox ViT baseline",
            lambda: timm.create_model("vit_base_patch16_224.orig_in21k_ft_in1k", pretrained=True),
            True,
        ),
    ]

    print("本脚本会把预训练模型缓存到项目目录内：")
    print("PRETRAINED_DIR =", PRETRAINED_DIR)
    print("HF_HOME =", HF_HOME)
    print("HUGGINGFACE_HUB_CACHE =", HF_HUB)
    print("TORCH_HOME =", TORCH_HOME)
    print("")
    print("下载完成后，请把整个 pretrained/ 文件夹随项目一起复制到服务器。")

    total_start = time.time()
    if tqdm is not None:
        with tqdm(total=len(steps), desc="整体下载进度", unit="step") as progress:
            for name, func, optional in steps:
                run_step(progress, name, func, optional)
    else:
        print("\n未安装 tqdm，将使用普通文本输出。")
        for idx, (name, func, optional) in enumerate(steps, start=1):
            print(f"\n[{idx}/{len(steps)}]")
            run_step(None, name, func, optional)

    total_elapsed = time.time() - total_start
    print("\n全部步骤完成。总耗时：", format_seconds(total_elapsed))
    print("缓存目录已准备好：", PRETRAINED_DIR)


if __name__ == "__main__":
    main()
