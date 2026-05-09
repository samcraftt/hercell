import os
from pathlib import Path
from tiatoolbox.models.engine.nucleus_predictor import NucleusInstanceSegmentor

def find_dataset():
    current_dir = Path(__file__).parent.resolve()
    
    primary_path = current_dir.parent / "her2-ihc-40x-wsi" / "WSI-based-dataset" / "train_data_wsi" / "class_3+"

    if primary_path.exists():
        return str(primary_path)
    else:
        return None

def run_segmentation():
    data_dir = find_dataset()
    output_dir = "./hovernet_results"

    if not data_dir:
        print("Error: Could not locate the dataset directory.")
        print("Please ensure 'bash download_data.sh' has been run successfully.")
        return

    print("--------------------------------------------------")
    print(f"Target Dataset: {data_dir}")
    print("--------------------------------------------------")
    print("Initializing HoVer-Net (fast-pannuke) segmentor...")
    
    segmentor = NucleusInstanceSegmentor(
        pretrained_model="hovernet_fast-pannuke",
        batch_size=4
    )

    print("Running automated cellular segmentation...")
    
    segmentor.predict(
        imgs=[data_dir],
        save_dir=output_dir,
        mode="tile",
        on_gpu=False, # Set to False for universal CPU compatibility
        crash_on_exception=False
    )
    
    print(f"\nSUCCESS: Nuclear segmentation complete. Results saved to {output_dir}/")

if __name__ == "__main__":
    run_segmentation()
