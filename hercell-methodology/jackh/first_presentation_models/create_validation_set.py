from pathlib import Path
import random
import shutil

random.seed(42)

DATA_DIR = Path("her2-ihc-40x-patch/Patch-based-dataset")
TRAIN_DIR = DATA_DIR / "train_data_patch"
VAL_DIR = DATA_DIR / "val_data_patch"

VAL_FRAC = 0.15

for class_dir in TRAIN_DIR.iterdir():
    if not class_dir.is_dir():
        continue

    val_class_dir = VAL_DIR / class_dir.name
    val_class_dir.mkdir(parents=True, exist_ok=True)

    images = [p for p in class_dir.iterdir() if p.is_file()]
    random.shuffle(images)

    n_val = int(len(images) * VAL_FRAC)
    val_images = images[:n_val]

    for img_path in val_images:
        shutil.move(str(img_path), str(val_class_dir / img_path.name))

    print(f"{class_dir.name}: moved {n_val} images to validation")

print("Done.")