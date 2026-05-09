import os
import argparse
from tiatoolbox.models.engine.nucleus_predictor import NucleusInstanceSegmentor

def run_segmentation(input_dir, output_dir):
    if not os.path.exists(input_dir):
        print(f"Error: Dataset directory '{input_dir}' not found.")
        print("Please ensure the data is downloaded via download_data.sh first.")
        return

    print(f"Initializing HoVer-Net (fast-pannuke) segmentor...")
    segmentor = NucleusInstanceSegmentor(
        pretrained_model="hovernet_fast-pannuke",
        batch_size=4
    )

    print(f"Running segmentation on images in: {input_dir}")
    segmentor.predict(
        imgs=[input_dir],
        save_dir=output_dir,
        mode="tile",
        on_gpu=False, # Defaulting to False for broad compatibility
        crash_on_exception=False
    )
    print(f"Segmentation complete. Results saved to {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run HoVer-Net Nucleus Segmentation")
    # By default, points to a theoretical data folder downloaded by their bash script
    parser.add_argument("--input", type=str, default="../data/wsi_patches", help="Path to input images")
    parser.add_argument("--output", type=str, default="./hovernet_results", help="Path to save output .dat files")
    
    args = parser.parse_args()
    run_segmentation(args.input, args.output)
