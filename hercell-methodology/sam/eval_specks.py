from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn

from generate_specks import generate_speck_sample


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
EVAL_SAMPLES = 1000
MODEL_PATH = "models/specks.pt"
OUT_FILE = "debug/eval_specks.png"
Path("debug").mkdir(parents=True, exist_ok=True)

CLS_0 = 0
CLS_1 = 1


class SpeckClassModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(3, 16, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
        )
        self.count_head = nn.Linear(64, 1)
        self.class_head = nn.Linear(64, 4)

    def forward(self, x):
        features = self.encoder(x)
        return self.count_head(features), self.class_head(features)


def image_to_tensor(image):
    image_np = np.array(image).astype(np.float32) / 255.0
    image_np = np.transpose(image_np, (2, 0, 1))
    return torch.tensor(image_np, dtype=torch.float32)


def main():
    model = SpeckClassModel().to(DEVICE)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()

    true_labels = []
    pred_labels = []
    prob_cls1_list = []

    with torch.no_grad():
        collected = 0
        while collected < EVAL_SAMPLES:
            image, _, true_class, _ = generate_speck_sample()
            if true_class not in (CLS_0, CLS_1):
                continue

            x = image_to_tensor(image).unsqueeze(0).to(DEVICE)
            _, pred_logits = model(x)
            probs = torch.softmax(pred_logits[0], dim=0).cpu().numpy()
            prob_cls1 = float(probs[CLS_1])
            pred_bin = CLS_1 if prob_cls1 >= 0.5 else CLS_0

            true_labels.append(true_class)
            pred_labels.append(pred_bin)
            prob_cls1_list.append(prob_cls1)
            collected += 1

    prob_cls1_arr = np.array(prob_cls1_list)
    true_arr = np.array(true_labels)
    pred_arr = np.array(pred_labels)
    correct = pred_arr == true_arr

    order = np.argsort(prob_cls1_arr)
    prob_sorted = prob_cls1_arr[order]
    true_sorted = true_arr[order]
    correct_sorted = correct[order]

    x_axis = np.arange(len(order))

    fig, ax = plt.subplots(figsize=(13, 7))

    ax.plot(
        x_axis,
        prob_sorted,
        color="#2a6496",
        linewidth=2.4,
        zorder=3,
        label="P(class 1)",
    )
    ax.axhline(
        y=0.5,
        color="#888888",
        linestyle=":",
        linewidth=1.5,
        zorder=4,
        label="Decision boundary (P = 0.5)",
    )

    ax.legend(loc="upper left", fontsize=12, framealpha=0.85)

    cls0_mask = true_sorted == CLS_0
    cls1_mask = true_sorted == CLS_1
    acc0 = float(correct_sorted[cls0_mask].mean()) if cls0_mask.any() else 0.0
    acc1 = float(correct_sorted[cls1_mask].mean()) if cls1_mask.any() else 0.0
    acc = float(correct_sorted.mean())
    summary = (
        f"class 0 acc:  {acc0:.1%}  (n={int(cls0_mask.sum())})\n"
        f"class 1 acc:  {acc1:.1%}  (n={int(cls1_mask.sum())})\n"
        f"Overall acc:  {acc:.1%}  (n={len(correct_sorted)})"
    )
    ax.text(
        0.99,
        0.97,
        summary,
        transform=ax.transAxes,
        fontsize=11,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.85),
    )

    ax.set_xlabel("Samples — sorted by P(class 1) ascending", fontsize=14)
    ax.set_ylabel("P(class 1)", fontsize=14)
    ax.set_title("Toy example · class 0 vs class 1 · prediction confidence", fontsize=17)
    ax.set_xlim(-0.5, len(x_axis) - 0.5)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.tick_params(axis="y", labelsize=12)

    plt.tight_layout()
    plt.savefig(OUT_FILE, dpi=150)
    print(f"Plot saved to {OUT_FILE}")
    plt.close(fig)

    print(f"Binary eval (threshold 0.5) on {EVAL_SAMPLES} class-0/class-1 samples")
    print(f"Overall accuracy: {acc:.4f}")


if __name__ == "__main__":
    main()
