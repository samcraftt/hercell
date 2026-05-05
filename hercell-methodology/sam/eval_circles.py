import numpy as np
import torch
import torch.nn as nn

from generate_circles import generate_circle_sample


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
EVAL_SAMPLES = 1000
MODEL_PATH = "models/circles.pt"


class CircleCountModel(nn.Module):
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
        return self.count_head(self.encoder(x))


def image_to_tensor(image):
    image_np = np.array(image).astype(np.float32) / 255.0
    image_np = np.transpose(image_np, (2, 0, 1))
    return torch.tensor(image_np, dtype=torch.float32)


def main():
    model = CircleCountModel().to(DEVICE)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()

    mae_raw_sum = 0.0
    mae_rounded_sum = 0.0
    exact_count = 0

    with torch.no_grad():
        for _ in range(EVAL_SAMPLES):
            image, true_count = generate_circle_sample()
            x = image_to_tensor(image).unsqueeze(0).to(DEVICE)
            pred = model(x).item()

            mae_raw_sum += abs(pred - true_count)
            pred_round = round(pred)
            mae_rounded_sum += abs(pred_round - true_count)
            exact_count += int(pred_round == true_count)

    print(f"Evaluated on {EVAL_SAMPLES} generated samples")
    print(f"Raw count MAE: {mae_raw_sum / EVAL_SAMPLES:.4f}")
    print(f"Rounded count MAE: {mae_rounded_sum / EVAL_SAMPLES:.4f}")
    print(f"Exact-match accuracy: {exact_count / EVAL_SAMPLES:.4f}")


if __name__ == "__main__":
    main()
