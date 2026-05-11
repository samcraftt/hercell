from pathlib import Path
import json
import random

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms, models
from tqdm import tqdm
from PIL import Image
import numpy as np
from skimage.color import rgb2hed


# ----------------------------
# Config
# ----------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "og_data" / "Patch-based-dataset"
TRAIN_DIR = DATA_DIR / "train_data_patch"
VAL_DIR = DATA_DIR / "val_data_patch"
TEST_DIR = DATA_DIR / "test_data_patch"

SAVE_DIR = Path(__file__).resolve().parent / "saved_models"
SAVE_DIR.mkdir(exist_ok=True)

IMAGE_SIZE = 384
BATCH_SIZE = 16
EPOCHS = 10
LR = 1e-4

DAB_ALIGN_WEIGHT = 0.75
NEGATIVE_SPARSITY_WEIGHT = 0.05
BORDER_WEIGHT = 0.10

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# ----------------------------
# Helpers
# ----------------------------

def extract_dab_map(pil_img):
    img = pil_img.convert("RGB").resize((IMAGE_SIZE, IMAGE_SIZE))
    arr = np.array(img).astype(np.float32) / 255.0

    hed = rgb2hed(arr)
    dab = hed[:, :, 2]

    dab = dab - dab.min()
    dab = dab / (dab.max() + 1e-8)

    return dab.astype(np.float32)


image_tfms = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


# ----------------------------
# Dataset
# ----------------------------

class BinaryHER2DABDataset(Dataset):
    def __init__(self, root_dir, train=False):
        self.root_dir = Path(root_dir)
        self.train = train

        self.class_to_idx = {
            "class_0": 0,
            "class_1+": 1,
        }

        self.samples = []

        for class_name, label in self.class_to_idx.items():
            class_dir = self.root_dir / class_name

            if not class_dir.exists():
                raise FileNotFoundError(f"Missing folder: {class_dir}")

            for path in class_dir.iterdir():
                if path.is_file():
                    self.samples.append((path, label))

        if len(self.samples) == 0:
            raise RuntimeError(f"No images found in {self.root_dir}")

    def __len__(self):
        return len(self.samples)

    def augment(self, img):
        if random.random() < 0.5:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)

        if random.random() < 0.5:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)

        k = random.choice([0, 1, 2, 3])
        if k > 0:
            img = img.rotate(90 * k)

        return img

    def __getitem__(self, idx):
        path, label = self.samples[idx]

        img = Image.open(path).convert("RGB")

        if self.train:
            img = self.augment(img)

        dab = extract_dab_map(img)

        img_tensor = image_tfms(img)
        dab_tensor = torch.from_numpy(dab).unsqueeze(0)

        return img_tensor, torch.tensor(label).float(), dab_tensor, str(path)


# ----------------------------
# Model
# ----------------------------

class DABRegularizedHeatmapConvNeXtV2(nn.Module):
    def __init__(self, topk_frac=0.10):
        super().__init__()

        base = models.convnext_tiny(
            weights=models.ConvNeXt_Tiny_Weights.IMAGENET1K_V1
        )

        # Earlier ConvNeXt features give a higher-resolution heatmap.
        self.features = nn.Sequential(*list(base.features.children())[:6])

        # At this stage ConvNeXt-Tiny has 384 channels.
        self.heatmap_head = nn.Conv2d(384, 1, kernel_size=1)

        self.topk_frac = topk_frac

    def forward(self, x):
        features = self.features(x)
        heatmap_logits = self.heatmap_head(features)

        flat = heatmap_logits.flatten(start_dim=1)
        k = max(1, int(self.topk_frac * flat.shape[1]))

        image_logits = flat.topk(k, dim=1).values.mean(dim=1)

        return image_logits, heatmap_logits


# ----------------------------
# Loss
# ----------------------------

def compute_loss(image_logits, heatmap_logits, labels, dab_maps):
    cls_loss = F.binary_cross_entropy_with_logits(image_logits, labels)

    pred_heatmap = torch.sigmoid(heatmap_logits)

    dab_small = F.interpolate(
        dab_maps,
        size=pred_heatmap.shape[-2:],
        mode="bilinear",
        align_corners=False,
    )

    labels_view = labels.view(-1, 1, 1, 1)

    positive_mask = labels_view
    negative_mask = 1.0 - labels_view

    # Positive images: make learned heatmap overlap DAB signal.
    dab_weight = 1.0 + 3.0 * dab_small

    positive_count = positive_mask.sum().clamp(min=1.0)

    align_loss = (
        positive_mask
        * dab_weight
        * (pred_heatmap - dab_small).pow(2)
    ).mean() / positive_count

    # Negative images: discourage broad/random activation.
    negative_count = negative_mask.sum().clamp(min=1.0)

    negative_sparsity_loss = (
        negative_mask * pred_heatmap
    ).mean() / negative_count

    # Border penalty: discourage edge/corner shortcuts.
    border = torch.zeros_like(pred_heatmap)
    border[:, :, :2, :] = 1
    border[:, :, -2:, :] = 1
    border[:, :, :, :2] = 1
    border[:, :, :, -2:] = 1

    border_loss = (pred_heatmap * border).mean()

    total_loss = (
        cls_loss
        + DAB_ALIGN_WEIGHT * align_loss
        + NEGATIVE_SPARSITY_WEIGHT * negative_sparsity_loss
        + BORDER_WEIGHT * border_loss
    )

    return {
        "total": total_loss,
        "cls": cls_loss,
        "align": align_loss,
        "sparse": negative_sparsity_loss,
        "border": border_loss,
    }


# ----------------------------
# Training / evaluation
# ----------------------------

def train_one_epoch(model, loader, optimizer):
    model.train()

    totals = {
        "loss": 0.0,
        "cls": 0.0,
        "align": 0.0,
        "sparse": 0.0,
        "border": 0.0,
    }

    correct = 0
    total = 0

    for images, labels, dab_maps, paths in tqdm(loader, desc="Training"):
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)
        dab_maps = dab_maps.to(DEVICE)

        optimizer.zero_grad()

        image_logits, heatmap_logits = model(images)

        losses = compute_loss(image_logits, heatmap_logits, labels, dab_maps)

        losses["total"].backward()
        optimizer.step()

        probs = torch.sigmoid(image_logits)
        preds = (probs >= 0.5).float()

        batch_size = images.size(0)

        totals["loss"] += losses["total"].item() * batch_size
        totals["cls"] += losses["cls"].item() * batch_size
        totals["align"] += losses["align"].item() * batch_size
        totals["sparse"] += losses["sparse"].item() * batch_size
        totals["border"] += losses["border"].item() * batch_size

        correct += (preds == labels).sum().item()
        total += labels.size(0)

    return {
        "loss": totals["loss"] / total,
        "cls_loss": totals["cls"] / total,
        "align_loss": totals["align"] / total,
        "sparse_loss": totals["sparse"] / total,
        "border_loss": totals["border"] / total,
        "acc": correct / total,
    }


@torch.no_grad()
def evaluate(model, loader, desc="Evaluating"):
    model.eval()

    total_loss = 0.0
    correct = 0
    total = 0

    y_true = []
    y_prob = []
    y_pred = []
    image_paths = []

    for images, labels, dab_maps, paths in tqdm(loader, desc=desc):
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)
        dab_maps = dab_maps.to(DEVICE)

        image_logits, heatmap_logits = model(images)

        losses = compute_loss(image_logits, heatmap_logits, labels, dab_maps)

        probs = torch.sigmoid(image_logits)
        preds = (probs >= 0.5).float()

        total_loss += losses["total"].item() * images.size(0)
        correct += (preds == labels).sum().item()
        total += labels.size(0)

        y_true.extend(labels.cpu().tolist())
        y_prob.extend(probs.cpu().tolist())
        y_pred.extend(preds.cpu().tolist())
        image_paths.extend(paths)

    return {
        "loss": total_loss / total,
        "acc": correct / total,
        "y_true": y_true,
        "y_prob": y_prob,
        "y_pred": y_pred,
        "paths": image_paths,
    }


def main():
    print("Device:", DEVICE)
    print("Image size:", IMAGE_SIZE)
    print("Batch size:", BATCH_SIZE)

    train_ds = BinaryHER2DABDataset(TRAIN_DIR, train=True)
    val_ds = BinaryHER2DABDataset(VAL_DIR, train=False)
    test_ds = BinaryHER2DABDataset(TEST_DIR, train=False)

    print("Class mapping:", train_ds.class_to_idx)
    print("Train size:", len(train_ds))
    print("Val size:", len(val_ds))
    print("Test size:", len(test_ds))

    train_loader = DataLoader(
        train_ds,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=4,
        pin_memory=True,
    )

    val_loader = DataLoader(
        val_ds,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=4,
        pin_memory=True,
    )

    test_loader = DataLoader(
        test_ds,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=4,
        pin_memory=True,
    )

    model = DABRegularizedHeatmapConvNeXtV2(topk_frac=0.10).to(DEVICE)

    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)

    best_val_acc = 0.0
    best_model_path = SAVE_DIR / "dab_regularized_heatmap_convnext_v2_best.pt"

    for epoch in range(EPOCHS):
        print(f"\nEpoch {epoch + 1}/{EPOCHS}")

        train_stats = train_one_epoch(model, train_loader, optimizer)
        val_stats = evaluate(model, val_loader, desc="Validation")

        print(
            f"Train loss: {train_stats['loss']:.4f} | "
            f"cls: {train_stats['cls_loss']:.4f} | "
            f"align: {train_stats['align_loss']:.4f} | "
            f"sparse: {train_stats['sparse_loss']:.4f} | "
            f"border: {train_stats['border_loss']:.4f} | "
            f"acc: {train_stats['acc']:.4f}"
        )

        print(
            f"Val loss:   {val_stats['loss']:.4f} | "
            f"Val acc:   {val_stats['acc']:.4f}"
        )

        if val_stats["acc"] > best_val_acc:
            best_val_acc = val_stats["acc"]
            torch.save(model.state_dict(), best_model_path)
            print("Saved best V2 model.")

    print("\nLoading best model for final test...")
    model.load_state_dict(torch.load(best_model_path, map_location=DEVICE))

    test_stats = evaluate(model, test_loader, desc="Testing")

    print(f"\nTest loss: {test_stats['loss']:.4f} | Test acc: {test_stats['acc']:.4f}")

    with open(PROJECT_ROOT / "dab_regularized_heatmap_v2_test_predictions.json", "w") as f:
        json.dump(test_stats, f, indent=2)

    print("Saved predictions to dab_regularized_heatmap_v2_test_predictions.json")
    print(f"Best model saved to {best_model_path}")


if __name__ == "__main__":
    main()