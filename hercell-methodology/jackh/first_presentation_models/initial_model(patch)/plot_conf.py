from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
import matplotlib.pyplot as plt
import numpy as np

DATA_DIR = Path("her2-ihc-40x-patch/Patch-based-dataset")
MODEL_PATH = Path("saved_models/convnext_her2_best.pt")

IMAGE_SIZE = 224
BATCH_SIZE = 32
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

CLASS_0 = "class_0"
CLASS_1 = "class_1+"


eval_tfms = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])


def build_model():
    model = models.convnext_tiny(weights=None)
    in_features = model.classifier[2].in_features
    model.classifier[2] = nn.Linear(in_features, 4)
    return model


@torch.no_grad()
def main():
    ds = datasets.ImageFolder(DATA_DIR / "test_data_patch", transform=eval_tfms)

    class_to_idx = ds.class_to_idx
    idx_0 = class_to_idx[CLASS_0]
    idx_1 = class_to_idx[CLASS_1]

    loader = DataLoader(ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=4)

    model = build_model().to(DEVICE)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()

    probs_1 = []
    true_labels = []

    for images, labels in loader:
        images = images.to(DEVICE)
        logits = model(images)

        probs = torch.softmax(logits, dim=1)

        probs_1.extend(probs[:, idx_1].cpu().numpy())
        true_labels.extend(labels.numpy())

    probs_1 = np.array(probs_1)
    true_labels = np.array(true_labels)

    mask = (true_labels == idx_0) | (true_labels == idx_1)
    probs_1 = probs_1[mask]
    true_labels = true_labels[mask]

    binary_true = (true_labels == idx_1).astype(int)
    binary_pred = (probs_1 >= 0.5).astype(int)

    correct = binary_true == binary_pred

    sort_idx = np.argsort(probs_1)
    probs_sorted = probs_1[sort_idx]
    correct_sorted = correct[sort_idx]
    true_sorted = binary_true[sort_idx]

    class0_mask = true_sorted == 0
    class1_mask = true_sorted == 1

    class0_acc = (binary_pred[binary_true == 0] == 0).mean()
    class1_acc = (binary_pred[binary_true == 1] == 1).mean()
    overall_acc = (binary_pred == binary_true).mean()

    n0 = (binary_true == 0).sum()
    n1 = (binary_true == 1).sum()
    n = len(binary_true)

    x = np.arange(len(probs_sorted))

    plt.figure(figsize=(18, 6))

    plt.plot(x, probs_sorted, label="P(class_1+)")
    plt.axhline(0.5, linestyle="--", color="gray", label="Decision boundary (P = 0.5)")

    wrong_idx = np.where(~correct_sorted)[0]
    plt.scatter(
        wrong_idx,
        probs_sorted[wrong_idx],
        marker="x",
        s=70,
        color="red",
        linewidths=2,
        label="Incorrect prediction",
    )

    text = (
        f"class_0 acc: {class0_acc * 100:.1f}%  (n={n0})\n"
        f"class_1+ acc: {class1_acc * 100:.1f}%  (n={n1})\n"
        f"Overall acc: {overall_acc * 100:.1f}%  (n={n})"
    )

    plt.text(
        0.86,
        0.93,
        text,
        transform=plt.gca().transAxes,
        fontsize=11,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.9),
    )

    plt.title("Patch Model · class_0 vs class_1+ · Prediction Confidence")
    plt.xlabel("Samples — sorted by P(class_1+) ascending")
    plt.ylabel("P(class_1+)")
    plt.ylim(0, 1)
    plt.legend(loc="upper left")
    plt.tight_layout()

    plt.savefig("patch_class0_vs_class1.png", dpi=200)
    plt.show()


if __name__ == "__main__":
    main()