from pathlib import Path
import json

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from sklearn.metrics import classification_report, confusion_matrix
from tqdm import tqdm

DATA_DIR = Path("her2-ihc-40x-patch/Patch-based-dataset")
SAVE_DIR = Path("saved_models")
SAVE_DIR.mkdir(exist_ok=True)

IMAGE_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 10
LR = 1e-4
NUM_CLASSES = 4

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


train_tfms = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.10, hue=0.02),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

eval_tfms = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])


def build_model():
    model = models.convnext_tiny(weights=models.ConvNeXt_Tiny_Weights.IMAGENET1K_V1)
    in_features = model.classifier[2].in_features
    model.classifier[2] = nn.Linear(in_features, NUM_CLASSES)
    return model


def train_one_epoch(model, loader, criterion, optimizer):
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for images, labels in tqdm(loader, desc="Training"):
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)

        optimizer.zero_grad()
        logits = model(images)
        loss = criterion(logits, labels)

        loss.backward()
        optimizer.step()

        total_loss += loss.item() * images.size(0)
        correct += (logits.argmax(1) == labels).sum().item()
        total += labels.size(0)

    return total_loss / total, correct / total


@torch.no_grad()
def evaluate(model, loader, criterion, desc="Evaluating"):
    model.eval()
    total_loss = 0
    correct = 0
    total = 0

    y_true = []
    y_pred = []

    for images, labels in tqdm(loader, desc=desc):
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)

        logits = model(images)
        loss = criterion(logits, labels)

        preds = logits.argmax(1)

        total_loss += loss.item() * images.size(0)
        correct += (preds == labels).sum().item()
        total += labels.size(0)

        y_true.extend(labels.cpu().tolist())
        y_pred.extend(preds.cpu().tolist())

    return total_loss / total, correct / total, y_true, y_pred


def main():
    print("Device:", DEVICE)

    train_ds = datasets.ImageFolder(DATA_DIR / "train_data_patch", transform=train_tfms)
    val_ds = datasets.ImageFolder(DATA_DIR / "val_data_patch", transform=eval_tfms)
    test_ds = datasets.ImageFolder(DATA_DIR / "test_data_patch", transform=eval_tfms)

    print("Classes:", train_ds.classes)
    print("Class mapping:", train_ds.class_to_idx)
    print("Train size:", len(train_ds))
    print("Val size:", len(val_ds))
    print("Test size:", len(test_ds))

    with open(SAVE_DIR / "class_to_idx.json", "w") as f:
        json.dump(train_ds.class_to_idx, f, indent=2)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=4, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=4, pin_memory=True)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=4, pin_memory=True)

    model = build_model().to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)

    best_val_acc = 0

    for epoch in range(EPOCHS):
        print(f"\nEpoch {epoch + 1}/{EPOCHS}")

        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer)
        val_loss, val_acc, _, _ = evaluate(model, val_loader, criterion, desc="Validation")

        print(f"Train loss: {train_loss:.4f} | Train acc: {train_acc:.4f}")
        print(f"Val loss:   {val_loss:.4f} | Val acc:   {val_acc:.4f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), SAVE_DIR / "convnext_her2_best.pt")
            print("Saved best model.")

    print("\nLoading best model for final test...")
    model.load_state_dict(torch.load(SAVE_DIR / "convnext_her2_best.pt", map_location=DEVICE))

    test_loss, test_acc, y_true, y_pred = evaluate(model, test_loader, criterion, desc="Testing")

    print(f"\nTest loss: {test_loss:.4f} | Test acc: {test_acc:.4f}")
    print("\nClassification report:")
    print(classification_report(y_true, y_pred, target_names=test_ds.classes))

    print("Confusion matrix:")
    print(confusion_matrix(y_true, y_pred))


if __name__ == "__main__":
    main()