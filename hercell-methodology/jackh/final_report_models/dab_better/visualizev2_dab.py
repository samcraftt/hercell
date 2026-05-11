from pathlib import Path

import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from skimage.color import rgb2hed
from scipy.ndimage import gaussian_filter


# ----------------------------
# Config
# ----------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE2_DIR = Path(__file__).resolve().parent

MODEL_PATH = PHASE2_DIR / "saved_models" / "dab_regularized_heatmap_convnext_v2_best.pt"

IMAGE_DIR = (
    PROJECT_ROOT
    / "og_data"
    / "Patch-based-dataset"
    / "test_data_patch"
    / "class_1+"
)

IMAGE_SIZE = 384
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Automatically pick first image.
# You can replace this with a specific filename later.
IMAGE_PATH = next(IMAGE_DIR.glob("*.png"))

OUTPUT_PATH = PROJECT_ROOT / "dab_regularized_learned_heatmap_v2_example.png"


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


eval_tfms = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


# ----------------------------
# Same architecture as training
# ----------------------------

class DABRegularizedHeatmapConvNeXtV2(nn.Module):
    def __init__(self, topk_frac=0.10):
        super().__init__()

        base = models.convnext_tiny(weights=None)

        self.features = nn.Sequential(*list(base.features.children())[:6])
        self.heatmap_head = nn.Conv2d(384, 1, kernel_size=1)

        self.topk_frac = topk_frac

    def forward(self, x):
        features = self.features(x)
        heatmap_logits = self.heatmap_head(features)

        flat = heatmap_logits.flatten(start_dim=1)
        k = max(1, int(self.topk_frac * flat.shape[1]))

        image_logits = flat.topk(k, dim=1).values.mean(dim=1)

        return image_logits, heatmap_logits


def main():
    print("Device:", DEVICE)
    print("Model:", MODEL_PATH)
    print("Image:", IMAGE_PATH)

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

    if not IMAGE_PATH.exists():
        raise FileNotFoundError(f"Image not found: {IMAGE_PATH}")

    model = DABRegularizedHeatmapConvNeXtV2(topk_frac=0.10).to(DEVICE)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()

    original = Image.open(IMAGE_PATH).convert("RGB")
    original_resized = original.resize((IMAGE_SIZE, IMAGE_SIZE))

    dab = extract_dab_map(original)

    x = eval_tfms(original).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        image_logit, heatmap_logits = model(x)

        prob_1plus = torch.sigmoid(image_logit).item()

        learned_heatmap = torch.sigmoid(heatmap_logits)[0, 0]
        learned_heatmap = learned_heatmap.cpu().numpy()

    heatmap_img = Image.fromarray((learned_heatmap * 255).astype(np.uint8))
    heatmap_img = heatmap_img.resize(
        (IMAGE_SIZE, IMAGE_SIZE),
        resample=Image.BILINEAR,
    )

    learned_heatmap = np.array(heatmap_img).astype(np.float32) / 255.0

    # Smooth for visualization
    learned_heatmap = gaussian_filter(learned_heatmap, sigma=1.2)
    learned_heatmap = learned_heatmap - learned_heatmap.min()
    learned_heatmap = learned_heatmap / (learned_heatmap.max() + 1e-8)

    plt.figure(figsize=(16, 4))

    plt.subplot(1, 4, 1)
    plt.imshow(original_resized)
    plt.title("Original")
    plt.axis("off")

    plt.subplot(1, 4, 2)
    plt.imshow(dab, cmap="gray")
    plt.title("DAB brown signal")
    plt.axis("off")

    plt.subplot(1, 4, 3)
    plt.imshow(learned_heatmap, cmap="hot")
    plt.title("V2 learned heatmap")
    plt.axis("off")

    plt.subplot(1, 4, 4)
    plt.imshow(original_resized)
    plt.imshow(learned_heatmap, cmap="hot", alpha=0.45)
    plt.title(f"Overlay\nP(class_1+)={prob_1plus:.3f}")
    plt.axis("off")

    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=200)
    plt.show()

    print(f"P(class_1+): {prob_1plus:.4f}")
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()