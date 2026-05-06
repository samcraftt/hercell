import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset, WeightedRandomSampler
from torchvision import datasets, transforms, models
import numpy as np
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────────────
DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")
IMG_SIZE    = 224
BATCH_SIZE  = 32
EPOCHS      = 20
LR          = 1e-4
NUM_CLASSES = 4

WSI_DATA_ROOT = "../datasets/WSI-based-dataset"
MODEL_OUT = "models/baseline.pt"
Path("models").mkdir(exist_ok=True)

train_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

test_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


# ── Reused: data loading with weighted sampling for class imbalance ───────────
def build_loaders(data_root):
    train_ds = datasets.ImageFolder(data_root, transform=train_tf)
    test_ds  = datasets.ImageFolder(data_root, transform=test_tf)

    train_indices = [
        idx for idx, (path, _) in enumerate(train_ds.samples)
        if "train" in Path(path).name.lower()
    ]
    test_indices = [
        idx for idx, (path, _) in enumerate(test_ds.samples)
        if "test" in Path(path).name.lower()
    ]
    if not train_indices or not test_indices:
        raise RuntimeError(
            "Could not split data by filename. Ensure files contain 'train' or 'test' in their names."
        )

    train_targets = [train_ds.samples[idx][1] for idx in train_indices]
    class_counts = np.bincount(train_targets)
    if np.any(class_counts == 0):
        raise RuntimeError("At least one class has zero train samples after filename split.")

    train_subset = Subset(train_ds, train_indices)
    test_subset = Subset(test_ds, test_indices)

    targets      = np.array(train_targets)
    weights      = 1.0 / class_counts[targets]
    sampler      = WeightedRandomSampler(weights, len(weights))

    train_loader = DataLoader(train_subset, batch_size=BATCH_SIZE, sampler=sampler, num_workers=0)
    test_loader  = DataLoader(test_subset,  batch_size=BATCH_SIZE, shuffle=False,   num_workers=0)
    return train_loader, test_loader


# ── Reused: training and evaluation loop ─────────────────────────────────────
def train(model, train_loader, test_loader, save_path):
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)
    criterion = nn.CrossEntropyLoss()
    best_acc  = 0.0

    for epoch in range(EPOCHS):
        model.train()
        total_loss, correct, total = 0.0, 0, 0
        for imgs, labels in train_loader:
            imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()
            out  = model(imgs)
            loss = criterion(out, labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * imgs.size(0)
            correct    += (out.argmax(1) == labels).sum().item()
            total      += imgs.size(0)
        scheduler.step()

        model.eval()
        val_correct, val_total = 0, 0
        with torch.no_grad():
            for imgs, labels in test_loader:
                imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
                val_correct += (model(imgs).argmax(1) == labels).sum().item()
                val_total   += imgs.size(0)

        train_acc = correct / total
        val_acc   = val_correct / val_total
        print(f"  Epoch {epoch+1:02d}/{EPOCHS} | loss: {total_loss/total:.4f} | train acc: {train_acc:.4f} | val acc: {val_acc:.4f}")

        if epoch > EPOCHS // 4 and val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), save_path)

    print(f"  Best val acc: {best_acc:.4f}  →  saved to {save_path}\n")


# ── Reused: ResNet50 backbone with 4-class head ───────────────────────────────
def build_model():
    model    = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
    model.fc = nn.Linear(model.fc.in_features, NUM_CLASSES)
    return model.to(DEVICE)


wsi_train_loader, wsi_test_loader = build_loaders(WSI_DATA_ROOT)
wsi_model = build_model()
train(wsi_model, wsi_train_loader, wsi_test_loader, MODEL_OUT)
