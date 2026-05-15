# 离线可视化命令示例：
# python visualize_mvp_cbm.py -c ./checkpoint/isic2018/test/best.pth -d isic2018 --data-path ./dataset/isic2018/ --gpu 0 -b 8 --max-samples 24
#
# 运行前要求：
# 1. 已经有训练得到的 best.pth。
# 2. 数据集目录存在，并包含 dataList.npy 和 labelList.npy。
# 3. 项目根目录下的 pretrained/ 已经包含 BiomedCLIP 和 timm ViT 本地缓存。
#
# 运行结果默认保存在 ./vis/<dataset>/：
#   samples/                 每张样本的 CBM 解释图
#   summary/confusion_matrix.png
#   summary/concept_score_heatmap.png
#   arrays/images.npy
#   arrays/logits.npy
#   arrays/probs.npy
#   arrays/pred.npy
#   arrays/gt.npy
#   arrays/concept_scores.npy
#
# 注意：
# 本脚本强制使用本地 pretrained/ 缓存，并阻止 HuggingFace/timm/open_clip 联网下载。

import argparse
import copy
import os
from pathlib import Path
from types import SimpleNamespace

from offline_pretrained import (
    HF_HOME,
    HF_HUB,
    TORCH_HOME,
    block_network_access,
    configure_offline_environment,
    require_train_mvpcbm_pretrained_cache,
)

os.environ["HF_HOME"] = HF_HOME
os.environ["HUGGINGFACE_HUB_CACHE"] = HF_HUB
os.environ["TORCH_HOME"] = TORCH_HOME
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["MVP_CBM_ALLOW_NETWORK"] = "0"
configure_offline_environment()
block_network_access()

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import timm
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from model import mvpcbm


BUSI_CONCEPTS = {
    "Echogenicity": [
        "Anechoic (completely dark, fluid-filled)",
        "Hypoechoic (slightly darker than surrounding tissue)",
        "Isoechoic (similar echogenicity to surrounding tissue)",
        "Hyperechoic (brighter than surrounding tissue)",
        "Markedly hyperechoic with shadowing",
    ],
    "Shape": [
        "Oval (smooth, regular edges)",
        "Round (circular, symmetric)",
        "Lobulated (irregular but with smooth transitions)",
        "Angular (sharp, distinct edges)",
        "Irregular (no definable shape, spiculated)",
    ],
    "Margin": [
        "Circumscribed (clear, well-defined borders)",
        "Fuzzy (slightly blurred borders)",
        "Microlobulated (small, multiple lobules at the edges)",
        "Obscured (poorly defined borders)",
        "Spiculated (spiky, radiating lines from the margin)",
    ],
    "Orientation": [
        "Parallel (aligned with the skin surface)",
        "Not parallel (perpendicular or non-aligned)",
        "Antiparallel (tilted away from the skin surface)",
        "Complex orientation with mixed alignment",
        "Variable orientation with no consistent pattern",
    ],
    "Posterior_Features": [
        "Enhancement (increased brightness behind the lesion)",
        "No significant change",
        "Shadowing (reduced echogenicity behind the lesion)",
        "Reverberation artifacts",
        "Echogenic foci with shadowing",
    ],
    "Surrounding_Tissue": [
        "Normal echotexture with no surrounding abnormalities",
        "Minimal surrounding tissue changes",
        "Increased echogenicity in surrounding tissue",
        "Decreased echogenicity or fibrosis around the lesion",
        "Significant architectural distortion of surrounding tissue",
    ],
}

CONCEPT_DICT = {
    "busi": BUSI_CONCEPTS,
}

CLASS_NAMES = {
    "busi": ["normal", "benign", "malignant"],
}

NUM_CLASSES = {
    "busi": 3,
}


class NpyImageDataset(Dataset):
    def __init__(self, data_path, transform=None, max_samples=None):
        self.data_path = Path(data_path)
        self.transform = transform
        self.data = np.load(self.data_path / "dataList.npy", mmap_mode="r", allow_pickle=False)
        self.labels = np.load(self.data_path / "labelList.npy", mmap_mode="r", allow_pickle=False)
        self.indices = np.arange(len(self.labels))
        if max_samples is not None:
            self.indices = self.indices[:max_samples]

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, index):
        real_index = self.indices[index]
        image = self.data[real_index]
        label = int(self.labels[real_index])
        if self.transform is not None:
            image = self.transform(image)
        return image, label


def flatten_concepts(concept_dict):
    names = []
    groups = []
    for group_name, concept_names in concept_dict.items():
        for concept_name in concept_names:
            names.append(f"{group_name}: {concept_name}")
            groups.append(group_name)
    return names, groups


def short_text(text, max_len=58):
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def tensor_to_image(tensor):
    array = tensor.detach().cpu().float().numpy()
    if array.ndim == 3:
        array = np.transpose(array, (1, 2, 0))
    if array.ndim == 2:
        array = np.expand_dims(array, axis=-1)
    if array.shape[-1] == 1:
        array = np.repeat(array, 3, axis=-1)
    array = array - np.min(array)
    denom = np.max(array)
    if denom > 0:
        array = array / denom
    return np.clip(array, 0, 1)


def softmax(array, axis=-1):
    array = array - np.max(array, axis=axis, keepdims=True)
    exp = np.exp(array)
    return exp / np.sum(exp, axis=axis, keepdims=True)


def make_confusion_matrix(gt, pred, class_names, output_path):
    num_classes = len(class_names)
    matrix = np.zeros((num_classes, num_classes), dtype=np.int64)
    for true_label, pred_label in zip(gt, pred):
        matrix[int(true_label), int(pred_label)] += 1

    fig, ax = plt.subplots(figsize=(5.5, 4.8))
    image = ax.imshow(matrix, cmap="Blues")
    ax.set_title("Confusion Matrix")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Ground Truth")
    ax.set_xticks(np.arange(num_classes), class_names, rotation=30, ha="right")
    ax.set_yticks(np.arange(num_classes), class_names)
    for row in range(num_classes):
        for col in range(num_classes):
            ax.text(col, row, str(matrix[row, col]), ha="center", va="center", color="black")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def make_concept_heatmap(concept_scores, concept_names, output_path, top_k=12):
    if concept_scores.size == 0:
        return
    top_k = min(top_k, concept_scores.shape[1])
    top_indices = np.argsort(np.mean(np.abs(concept_scores), axis=0))[-top_k:][::-1]
    heatmap = concept_scores[:, top_indices]
    labels = [short_text(concept_names[index], 42) for index in top_indices]

    fig_height = max(4.0, 0.32 * len(heatmap))
    fig, ax = plt.subplots(figsize=(12, fig_height))
    image = ax.imshow(heatmap, aspect="auto", cmap="coolwarm")
    ax.set_title("Top Concept Scores Across Samples")
    ax.set_xlabel("Concept")
    ax.set_ylabel("Sample")
    ax.set_xticks(np.arange(top_k), labels, rotation=45, ha="right")
    ax.set_yticks(np.arange(len(heatmap)))
    fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def make_sample_figure(image_tensor, logits, concept_scores, gt, pred, class_names, concept_names, output_path, top_k=8):
    probabilities = softmax(logits)
    top_k = min(top_k, len(concept_scores))
    top_indices = np.argsort(np.abs(concept_scores))[-top_k:][::-1]
    top_values = concept_scores[top_indices]
    top_labels = [short_text(concept_names[index], 64) for index in top_indices]

    fig = plt.figure(figsize=(14, 7))
    grid = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.35], height_ratios=[1.0, 1.0])

    ax_image = fig.add_subplot(grid[:, 0])
    ax_image.imshow(tensor_to_image(image_tensor))
    ax_image.axis("off")
    ax_image.set_title(
        f"GT: {class_names[int(gt)]} | Pred: {class_names[int(pred)]}",
        fontsize=12,
    )

    ax_prob = fig.add_subplot(grid[0, 1])
    y_pos = np.arange(len(class_names))
    ax_prob.barh(y_pos, probabilities, color="#4c78a8")
    ax_prob.set_yticks(y_pos, class_names)
    ax_prob.invert_yaxis()
    ax_prob.set_xlim(0, 1)
    ax_prob.set_xlabel("Probability")
    ax_prob.set_title("Class Prediction")
    for row, value in enumerate(probabilities):
        ax_prob.text(min(value + 0.02, 0.98), row, f"{value:.2f}", va="center")

    ax_concept = fig.add_subplot(grid[1, 1])
    concept_y = np.arange(top_k)
    colors = ["#59a14f" if value >= 0 else "#e15759" for value in top_values]
    ax_concept.barh(concept_y, top_values, color=colors)
    ax_concept.set_yticks(concept_y, top_labels)
    ax_concept.invert_yaxis()
    ax_concept.axvline(0, color="black", linewidth=0.8)
    ax_concept.set_xlabel("Concept score")
    ax_concept.set_title("Top CBM Concepts")

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def build_model(args, concept_list, config):
    net = mvpcbm(concept_list=concept_list, model_name="biomedclip", config=config)
    vit = timm.create_model("vit_base_patch16_224", pretrained=True, num_classes=config.num_class)
    vit.head = nn.Identity()
    net.model.visual.trunk.load_state_dict(vit.state_dict())
    state_dict = torch.load(args.checkpoint, map_location="cpu")
    net.load_state_dict(state_dict)
    net.cuda()
    net.eval()
    return net


def run_inference(net, dataloader):
    images = []
    logits = []
    gt = []
    concept_scores = []
    captured_cls_inputs = []

    def capture_cls_input(module, inputs):
        captured_cls_inputs.append(inputs[0].detach())

    hook = net.cls_head.register_forward_pre_hook(capture_cls_input)
    try:
        with torch.no_grad():
            for batch_images, batch_labels in dataloader:
                images.append(batch_images.cpu())
                gt.append(batch_labels.numpy())
                batch_images = batch_images.cuda()
                batch_logits, _, _ = net(batch_images)
                logits.append(batch_logits.detach().cpu())
                concept_scores.append(captured_cls_inputs.pop(0).cpu())
    finally:
        hook.remove()

    return {
        "images": torch.cat(images, dim=0),
        "logits": torch.cat(logits, dim=0).numpy(),
        "gt": np.concatenate(gt, axis=0).astype(np.int64),
        "concept_scores": torch.cat(concept_scores, dim=0).numpy(),
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Offline MVP-CBM visualization from best.pth.")
    parser.add_argument("-c", "--checkpoint", required=True, help="Path to best.pth.")
    parser.add_argument("-d", "--dataset", default="busi", choices=sorted(CONCEPT_DICT.keys()))
    parser.add_argument("--data-path", required=True, help="Dataset directory containing dataList.npy and labelList.npy.")
    parser.add_argument("--gpu", default="0", help="CUDA_VISIBLE_DEVICES value.")
    parser.add_argument("-b", "--batch-size", type=int, default=8)
    parser.add_argument("--max-samples", type=int, default=24, help="Number of samples to visualize.")
    parser.add_argument("--top-k", type=int, default=8, help="Top concepts shown per sample.")
    parser.add_argument("--out-dir", default=None, help="Output directory. Default: ./vis/<dataset>/")
    return parser.parse_args()


def main():
    args = parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu
    require_train_mvpcbm_pretrained_cache()

    output_dir = Path(args.out_dir or Path("vis") / args.dataset)
    samples_dir = output_dir / "samples"
    summary_dir = output_dir / "summary"
    arrays_dir = output_dir / "arrays"
    samples_dir.mkdir(parents=True, exist_ok=True)
    summary_dir.mkdir(parents=True, exist_ok=True)
    arrays_dir.mkdir(parents=True, exist_ok=True)

    concept_list = CONCEPT_DICT[args.dataset]
    concept_names, _ = flatten_concepts(concept_list)
    class_names = CLASS_NAMES[args.dataset]
    config = SimpleNamespace(dataset=args.dataset, num_class=NUM_CLASSES[args.dataset])

    net = build_model(args, concept_list, config)
    val_transform = copy.deepcopy(config.preprocess)
    val_transform.transforms.insert(0, transforms.ToPILImage())

    dataset = NpyImageDataset(args.data_path, transform=val_transform, max_samples=args.max_samples)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, num_workers=0, drop_last=False)
    outputs = run_inference(net, dataloader)

    probs = softmax(outputs["logits"], axis=1)
    pred = np.argmax(outputs["logits"], axis=1).astype(np.int64)

    np.save(arrays_dir / "images.npy", outputs["images"].numpy())
    np.save(arrays_dir / "logits.npy", outputs["logits"])
    np.save(arrays_dir / "probs.npy", probs)
    np.save(arrays_dir / "pred.npy", pred)
    np.save(arrays_dir / "gt.npy", outputs["gt"])
    np.save(arrays_dir / "concept_scores.npy", outputs["concept_scores"])

    make_confusion_matrix(outputs["gt"], pred, class_names, summary_dir / "confusion_matrix.png")
    make_concept_heatmap(
        outputs["concept_scores"],
        concept_names,
        summary_dir / "concept_score_heatmap.png",
        top_k=max(args.top_k, 12),
    )

    for index in range(len(outputs["gt"])):
        make_sample_figure(
            outputs["images"][index],
            outputs["logits"][index],
            outputs["concept_scores"][index],
            outputs["gt"][index],
            pred[index],
            class_names,
            concept_names,
            samples_dir / f"sample_{index:04d}_gt{outputs['gt'][index]}_pred{pred[index]}.png",
            top_k=args.top_k,
        )

    acc = float(np.mean(pred == outputs["gt"]) * 100.0)
    print("Visualization complete.")
    print("Output directory:", output_dir)
    print(f"Samples: {len(outputs['gt'])}")
    print(f"Accuracy on visualized samples: {acc:.2f}%")


if __name__ == "__main__":
    main()
