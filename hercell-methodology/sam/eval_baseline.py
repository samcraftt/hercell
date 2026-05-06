import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms, models
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")
IMG_SIZE    = 224
NUM_CLASSES = 4
WSI_TEST    = "WSI-based-dataset/test_data_wsi"
BATCH_SIZE  = 64
MODEL_PATH  = "models/baseline.pt"
OUT_FILE    = "debug/eval_baseline.png"
Path("debug").mkdir(exist_ok=True)

test_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


def build_model():
    model    = models.resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, NUM_CLASSES)
    return model.to(DEVICE)


def run_inference(model, dataset, indices):
    subset = Subset(dataset, indices)
    loader = DataLoader(subset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    all_probs = []
    all_preds = []
    model.eval()
    with torch.no_grad():
        for imgs, _ in loader:
            imgs = imgs.to(DEVICE)
            probs = torch.softmax(model(imgs), dim=1)
            all_probs.append(probs.cpu())
            all_preds.extend(probs.argmax(1).cpu().tolist())
    return torch.cat(all_probs, dim=0), all_preds


def main():
    # Evaluate only held-out WSI samples (not seen during training).
    dataset     = datasets.ImageFolder(WSI_TEST, transform=test_tf)
    class_names = dataset.classes  # ['class_0', 'class_1+', 'class_2+', 'class_3+']

    cls0_idx = class_names.index("class_0")
    cls1_idx = class_names.index("class_1+")

    # Collect all class_0 and class_1+ sample indices
    indices     = []
    true_labels = []
    for idx, (_, label) in enumerate(dataset.samples):
        if label in (cls0_idx, cls1_idx):
            indices.append(idx)
            true_labels.append(label)

    print(f"Running inference on {len(indices)} samples "
          f"({true_labels.count(cls0_idx)} class_0, "
          f"{true_labels.count(cls1_idx)} class_1+)...")

    model = build_model()
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))

    all_probs, pred_labels = run_inference(model, dataset, indices)
    prob_cls1 = all_probs[:, cls1_idx].numpy()

    correct = np.array([p == t for p, t in zip(pred_labels, true_labels)])
    true_arr = np.array(true_labels)

    # Sort everything by P(class_1+) ascending
    order    = np.argsort(prob_cls1)
    prob_cls1_sorted = prob_cls1[order]
    true_sorted      = true_arr[order]
    correct_sorted   = correct[order]

    x = np.arange(len(order))

    # ── Plot ──────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(13, 7))

    # Main probability line
    ax.plot(x, prob_cls1_sorted, color="#2a6496", linewidth=2.4,
            zorder=3, label="P(class_1+)")

    # Horizontal decision-boundary line
    ax.axhline(y=0.5, color="#888888", linestyle="--", linewidth=1.5,
               zorder=4, label="Decision boundary (P = 0.5)")

    ax.legend(loc="upper left", fontsize=12, framealpha=0.85)

    # Accuracy summary in text box
    n_correct = correct_sorted.sum()
    acc = n_correct / len(correct_sorted)
    cls0_mask = true_sorted == cls0_idx
    cls1_mask = true_sorted == cls1_idx
    acc0 = correct_sorted[cls0_mask].mean()
    acc1 = correct_sorted[cls1_mask].mean()
    summary = (
        f"class_0 acc:  {acc0:.1%}  (n={cls0_mask.sum()})\n"
        f"class_1+ acc: {acc1:.1%}  (n={cls1_mask.sum()})\n"
        f"Overall acc:  {acc:.1%}  (n={len(correct_sorted)})"
    )
    ax.text(0.99, 0.97, summary, transform=ax.transAxes,
            fontsize=11, verticalalignment="top", horizontalalignment="right",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.85))

    ax.set_xlabel("Samples — sorted by P(class_1+) ascending", fontsize=14)
    ax.set_ylabel("P(class_1+)", fontsize=14)
    ax.set_title("WSI Model · class_0 vs class_1+ · Prediction Confidence", fontsize=17)
    ax.set_xlim(-0.5, len(x) - 0.5)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.tick_params(axis="y", labelsize=12)

    plt.tight_layout()
    plt.savefig(OUT_FILE, dpi=150)
    print(f"Plot saved to {OUT_FILE}")
    plt.close(fig)


if __name__ == "__main__":
    main()
