# Run the mock MVP

In one terminal, run:
```bash
cd hercell-app/backend
npm i
npm run dev
```

In another, run:
```bash
cd hercell-app/frontend
npm i
npm start
```

Upload images found in `hercell/hercell-app/images` to test functionality.

# Explore the methodology

1. `cd` into the `hercell-methodology` directory
2. Create a virtual environment and download dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
3. Download the datasets by running `bash download_data.sh`

## Toy example (Sam)

```bash
cd sam
```

### Baseline

```bash
python train_baseline.py    # ~10 hours
python eval_baseline.py     # ~20 minutes
```

### Toy example: cell segmentation and counting

```bash
python train_circles.py
python eval_circles.py
```

### Toy example: segmentation, counting, and HER2 "speck" detection

```bash
python train_specks.py      # ~20 minutes
python eval_specks.py
```

## Cell granularity (Jack)

```bash
python run_hovernet.py
```

## Jack H's code...

# Contributions

Sam's responsible for code in `hercell-methodology/sam`, Jack C in `hercell-methodology/jackc`, Jack H in `hercell-methodology/jackh`.
