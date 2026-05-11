from pathlib import Path
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt

CSV_PATH = Path("wsi_predictions.csv")
IMAGE_ROOT = Path("her2-ihc-40x-wsi/WSI-based-dataset/test_data_wsi")
HEATMAP_DIR = Path("heatmaps_class0_candidates")

df = pd.read_csv(CSV_PATH)

# Pick the most suspicious class_0 image
row = (
    df[df["true_class"] == "class_0"]
    .sort_values("p_class_1plus", ascending=False)
    .iloc[0]
)

img_path = IMAGE_ROOT / row["true_class"] / row["slide_id"]

# Find corresponding heatmap file
matches = list(HEATMAP_DIR.glob(f"*{row['slide_id']}"))

print("Image:", img_path)
print("P(class_1+):", row["p_class_1plus"])
print("Heatmap matches:", matches)

if len(matches) == 0:
    raise FileNotFoundError("No heatmap found. Run batch_heatmaps.py first.")

heatmap_path = matches[0]

original = Image.open(img_path).convert("RGB")
heatmap = Image.open(heatmap_path).convert("RGB")

plt.figure(figsize=(10, 5))

plt.subplot(1, 2, 1)
plt.imshow(original)
plt.title(f"Original\n{row['slide_id']}")
plt.axis("off")

plt.subplot(1, 2, 2)
plt.imshow(heatmap)
plt.title(f"Class_1+ heatmap\nP(1+)={row['p_class_1plus']:.3f}")
plt.axis("off")

plt.tight_layout()
plt.savefig("single_heatmap_example.png", dpi=200)
plt.show()