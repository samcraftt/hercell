from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from skimage.color import rgb2hed
from scipy.ndimage import gaussian_filter

IMAGE_PATH = Path("her2-ihc-40x-wsi/WSI-based-dataset/test_data_wsi/class_0/her2-0-score_test_1294.png")

img = Image.open(IMAGE_PATH).convert("RGB").resize((224, 224))
rgb = np.array(img).astype(np.float32) / 255.0

hed = rgb2hed(rgb)
dab = hed[:, :, 2]

dab = dab - dab.min()
dab = dab / (dab.max() + 1e-8)

# Smooth slightly so it looks like a heatmap instead of pixel noise
dab_smooth = gaussian_filter(dab, sigma=1.2)

plt.figure(figsize=(12, 4))

plt.subplot(1, 3, 1)
plt.imshow(img)
plt.title("Original")
plt.axis("off")

plt.subplot(1, 3, 2)
plt.imshow(dab, cmap="gray")
plt.title("DAB brown signal")
plt.axis("off")

plt.subplot(1, 3, 3)
plt.imshow(img)
plt.imshow(dab_smooth, cmap="hot", alpha=0.45)
plt.title("DAB overlay heatmap")
plt.axis("off")

plt.tight_layout()
plt.savefig("dab_overlay_heatmap.png", dpi=200)
plt.show()