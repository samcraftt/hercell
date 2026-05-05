echo "Downloading datasets"
mkdir -p datasets
cd datasets
curl -L "https://zenodo.org/api/records/15179608/files-archive" -o datasets.zip
unzip datasets.zip >/dev/null
rm datasets.zip
unzip her2-ihc-40x-patch.zip >/dev/null
rm her2-ihc-40x-patch.zip
unzip her2-ihc-40x-wsi.zip >/dev/null
rm her2-ihc-40x-wsi.zip
cd Patch-based-dataset
unzip test_data_patch.zip >/dev/null
rm test_data_patch.zip
unzip train_data_patch.zip >/dev/null
rm train_data_patch.zip
cd ../WSI-based-dataset
unzip test_data_wsi.zip >/dev/null
rm test_data_wsi.zip
unzip train_data_wsi.zip >/dev/null
rm train_data_wsi.zip
echo "Download complete"
