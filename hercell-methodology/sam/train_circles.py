import numpy as np
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from generate_circles import generate_circle_sample


TRAIN_SAMPLES = 4000
VAL_SAMPLES = 500
BATCH_SIZE = 32
EPOCHS = 12
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
Path("models").mkdir(exist_ok=True)


def generate_sample():
    image, blue_count = generate_circle_sample()
    image = np.array(image).astype(np.float32) / 255.0
    image = np.transpose(image, (2, 0, 1))
    return (
        torch.tensor(image, dtype=torch.float32),
        torch.tensor([blue_count], dtype=torch.float32),
    )


class CircleDataset(Dataset):
    def __init__(self, n):
        self.samples = [generate_sample() for _ in range(n)]

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]


class BlueCircleModel(nn.Module):
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
        )

        self.count_head = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(64, 1),
        )

    def forward(self, x):
        features = self.encoder(x)
        count = self.count_head(features)
        return count


train_dataset = CircleDataset(TRAIN_SAMPLES)
val_dataset = CircleDataset(VAL_SAMPLES)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)

model = BlueCircleModel().to(DEVICE)
count_loss_fn = nn.MSELoss()

optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

for epoch in range(EPOCHS):
    print(f'Starting epoch {epoch + 1}')
    model.train()
    train_loss = 0.0

    for images, counts in train_loader:
        images = images.to(DEVICE)
        counts = counts.to(DEVICE)

        pred_counts = model(images)
        loss = count_loss_fn(pred_counts, counts)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        train_loss += loss.item()

    model.eval()
    mae = 0.0

    with torch.no_grad():
        for images, counts in val_loader:
            images = images.to(DEVICE)
            counts = counts.to(DEVICE)

            pred_counts = model(images)
            mae += torch.abs(pred_counts - counts).sum().item()

    mae /= len(val_dataset)

    print(
        f"Epoch {epoch + 1}/{EPOCHS} | "
        f"Train Count Loss: {train_loss / len(train_loader):.4f} | "
        f"Val Count MAE: {mae:.4f}"
    )


torch.save(model.state_dict(), "models/circles.pt")
print("Saved model to models/circles.pt")
