# Up epochs from 12 to 100
# Takes 33 minutes, but worth a shot since accuracy is still increasing

import numpy as np
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from generate_specks import generate_speck_sample

TRAIN_SAMPLES = 4000
VAL_SAMPLES = 500
BATCH_SIZE = 32
EPOCHS = 100
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
Path("models").mkdir(exist_ok=True)


def generate_sample():
    image, blue_count, brown_class, _ = generate_speck_sample()
    image_np = np.array(image).astype(np.float32) / 255.0
    image_np = np.transpose(image_np, (2, 0, 1))

    return (
        torch.tensor(image_np, dtype=torch.float32),
        torch.tensor([blue_count], dtype=torch.float32),
        torch.tensor(brown_class, dtype=torch.long),
    )


class DotDataset(Dataset):
    def __init__(self, n):
        self.samples = [generate_sample() for _ in range(n)]

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]


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
        pred_count = self.count_head(features)
        pred_class_logits = self.class_head(features)
        return pred_count, pred_class_logits


train_dataset = DotDataset(TRAIN_SAMPLES)
val_dataset = DotDataset(VAL_SAMPLES)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)

model = SpeckClassModel().to(DEVICE)
count_loss_fn = nn.MSELoss()
class_loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

for epoch in range(EPOCHS):
    print(f"Starting epoch {epoch + 1}")
    model.train()
    train_loss = 0.0

    for images, blue_counts, brown_classes in train_loader:
        images = images.to(DEVICE)
        blue_counts = blue_counts.to(DEVICE)
        brown_classes = brown_classes.to(DEVICE)

        pred_counts, pred_class_logits = model(images)

        count_loss = count_loss_fn(pred_counts, blue_counts)
        class_loss = class_loss_fn(pred_class_logits, brown_classes)
        loss = class_loss + 0.2 * count_loss

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        train_loss += loss.item()

    model.eval()
    val_mae = 0.0
    val_correct = 0
    val_total = 0

    with torch.no_grad():
        for images, blue_counts, brown_classes in val_loader:
            images = images.to(DEVICE)
            blue_counts = blue_counts.to(DEVICE)
            brown_classes = brown_classes.to(DEVICE)

            pred_counts, pred_class_logits = model(images)
            val_mae += torch.abs(pred_counts - blue_counts).sum().item()

            pred_classes = pred_class_logits.argmax(dim=1)
            val_correct += (pred_classes == brown_classes).sum().item()
            val_total += brown_classes.size(0)

    val_mae /= len(val_dataset)
    val_acc = val_correct / val_total

    print(
        f"Epoch {epoch + 1}/{EPOCHS} | "
        f"Train Loss: {train_loss / len(train_loader):.4f} | "
        f"Val Blue Count MAE: {val_mae:.4f} | "
        f"Val Brown Class Acc: {val_acc:.4f}"
    )


torch.save(model.state_dict(), "models/specks.pt")
print("Saved model to models/specks.pt")
