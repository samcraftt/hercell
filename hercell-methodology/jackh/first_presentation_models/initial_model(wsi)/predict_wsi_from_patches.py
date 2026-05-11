from pathlib import Path
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import pandas as pd
from tqdm import tqdm

MODEL_PATH = Path("saved_models/convnext_her2_best.pt")
WSI_DIR = Path("her2-ihc-40x-wsi/WSI-based-dataset/test_data_wsi")

IMAGE_SIZE = 224
NUM_CLASSES = 4
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

CLASS_NAMES = ["class_0", "class_1+", "class_2+", "class_3+"]


eval_tfms = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


def build_model():
    model = models.convnext_tiny(weights=None)
    in_features = model.classifier[2].in_features
    model.classifier[2] = nn.Linear(in_features, NUM_CLASSES)
    return model


@torch.no_grad()
def predict_patch(model, img_path):
    img = Image.open(img_path).convert("RGB")
    x = eval_tfms(img).unsqueeze(0).to(DEVICE)

    logits = model(x)
    probs = torch.softmax(logits, dim=1).squeeze(0)

    return probs.cpu()


@torch.no_grad()
def predict_slide(model, slide_dir):
    patch_paths = []
    for ext in ["*.png", "*.jpg", "*.jpeg", "*.tif", "*.tiff"]:
        patch_paths.extend(slide_dir.glob(ext))

    if len(patch_paths) == 0:
        return None

    all_probs = []

    for patch_path in patch_paths:
        probs = predict_patch(model, patch_path)
        all_probs.append(probs)

    all_probs = torch.stack(all_probs)

    # Normal slide-level prediction
    mean_probs = all_probs.mean(dim=0)

    # Ultralow-style score: average of top 5% most class_1+-like patches
    p_1plus = all_probs[:, 1]
    k = max(1, int(0.05 * len(p_1plus)))
    topk_score = torch.topk(p_1plus, k).values.mean().item()

    pred_idx = int(mean_probs.argmax())

    return {
        "num_patches": len(patch_paths),
        "predicted_class": CLASS_NAMES[pred_idx],
        "p_class_0": mean_probs[0].item(),
        "p_class_1plus": mean_probs[1].item(),
        "p_class_2plus": mean_probs[2].item(),
        "p_class_3plus": mean_probs[3].item(),
        "ultralow_top5_score": topk_score,
    }


def main():
    print("Device:", DEVICE)

    model = build_model().to(DEVICE)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()

    rows = []

    for class_dir in WSI_DIR.iterdir():
        if not class_dir.is_dir():
            continue

        true_class = class_dir.name

        for img_path in tqdm(list(class_dir.glob("*")), desc=true_class):
            if not img_path.is_file():
                continue

            probs = predict_patch(model, img_path)

            result = {
                "slide_id": img_path.name,
                "true_class": true_class,
                "predicted_class": CLASS_NAMES[int(probs.argmax())],
                "p_class_0": probs[0].item(),
                "p_class_1plus": probs[1].item(),
                "p_class_2plus": probs[2].item(),
                "p_class_3plus": probs[3].item(),
                "ultralow_top5_score": probs[1].item(),  # just use P(1+) here
            }

            rows.append(result)
    
    df = pd.DataFrame(rows)
    df.to_csv("wsi_predictions.csv", index=False)

    print(df.head())
    print("Saved to wsi_predictions.csv")


if __name__ == "__main__":
    main()