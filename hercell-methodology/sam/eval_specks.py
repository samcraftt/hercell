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
    prob_cls0_list = []
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
            pred_4class = int(np.argmax(probs))

            true_labels.append(true_class)
            pred_labels.append(pred_4class)
            prob_cls0_list.append(float(probs[CLS_0]))
            prob_cls1_list.append(float(probs[CLS_1]))
            collected += 1

    prob_cls0 = np.array(prob_cls0_list)
    prob_cls1 = np.array(prob_cls1_list)
    true_arr = np.array(true_labels)
    pred_arr = np.array(pred_labels)

    # Restrict prediction to {class 0, class 1} by renormalizing those two
    # probabilities: P(class 1 | {class 0, class 1}) = p1 / (p0 + p1).
    denom = prob_cls0 + prob_cls1
    prob_cls1_given_01 = np.divide(
        prob_cls1,
        denom,
        out=np.full_like(prob_cls1, 0.5),
        where=denom > 0,
    )

    # Keep only samples the model predicts as class 0 (4-class argmax).
    keep_mask = pred_arr == CLS_0
    if not keep_mask.any():
        raise RuntimeError("No samples were predicted as class 0 by the specks model.")

    prob_kept = prob_cls1_given_01[keep_mask]
    true_kept = true_arr[keep_mask]

    order = np.argsort(prob_kept)
    prob_cls1_sorted = prob_kept[order]
    true_sorted = true_kept[order]

    x_axis = np.arange(len(order))

    fig, ax = plt.subplots(figsize=(13, 7))

    ax.plot(
        x_axis,
        prob_cls1_sorted,
        color="#2a6496",
        linewidth=2.4,
        zorder=3,
        label="P(class 1 | {class 0, class 1})",
    )

    ax.legend(loc="upper left", fontsize=12, framealpha=0.85)

    n_total = len(true_sorted)
    cls0_mask = true_sorted == CLS_0
    cls1_mask = true_sorted == CLS_1
    precision_cls0 = cls0_mask.mean()
    miss_rate_cls1 = cls1_mask.mean()
    summary = (
        f"Predicted class 0 samples: {n_total}\n"
        f"True class 0 among them:   {precision_cls0:.1%}  (n={int(cls0_mask.sum())})\n"
        f"True class 1 among them:   {miss_rate_cls1:.1%}  (n={int(cls1_mask.sum())})"
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

    ax.set_xlabel(
        "Specks-predicted class 0 samples — sorted by P(class 1 | {class 0, class 1})",
        fontsize=14,
    )
    ax.set_ylabel("P(class 1 | {class 0, class 1})", fontsize=14)
    ax.set_title(
        "Specks-Predicted class 0 Samples · 0 vs 1 Conditional Score",
        fontsize=17,
    )
    ax.set_xlim(-0.5, len(x_axis) - 0.5)
    ax.set_ylim(0, 0.5)
    ax.set_xticks([])
    ax.tick_params(axis="y", labelsize=12)

    plt.tight_layout()
    plt.savefig(OUT_FILE, dpi=150)
    print(f"Plot saved to {OUT_FILE}")
    plt.close(fig)

    above_thresh = int((prob_cls1_sorted > 0.05).sum())
    print(
        f"Predicted class 0 samples with P(class 1 | {{class 0, class 1}}) > 0.05: "
        f"{above_thresh} / {n_total}"
    )


if __name__ == "__main__":
    main()
