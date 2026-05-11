import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("wsi_predictions.csv")

# Keep only class_0 and class_1+
df = df[df["true_class"].isin(["class_0", "class_1+"])].copy()

# Binary labels
df["y_true"] = (df["true_class"] == "class_1+").astype(int)
df["y_pred"] = (df["p_class_1plus"] >= 0.5).astype(int)

df["correct"] = df["y_true"] == df["y_pred"]

# Sort by confidence
df = df.sort_values("p_class_1plus")

x = np.arange(len(df))
y = df["p_class_1plus"].values

# Accuracy stats
class0 = df[df["y_true"] == 0]
class1 = df[df["y_true"] == 1]

class0_acc = (class0["y_pred"] == 0).mean()
class1_acc = (class1["y_pred"] == 1).mean()
overall_acc = (df["correct"]).mean()

# Plot
plt.figure(figsize=(18, 6))

plt.plot(x, y, label="P(class_1+)")
plt.axhline(0.5, linestyle="--", color="gray", label="Decision boundary (P = 0.5)")

# Mark incorrect
wrong = df[~df["correct"]]
wrong_idx = wrong.index.to_numpy()
sorted_idx = df.index.to_numpy()

# map original indices to sorted positions
pos = {idx: i for i, idx in enumerate(sorted_idx)}
wrong_x = [pos[i] for i in wrong_idx]

plt.scatter(
    wrong_x,
    wrong["p_class_1plus"],
    marker="x",
    s=70,
    color="red",
    linewidths=2,
    label="Incorrect prediction",
)

# Text box
text = (
    f"class_0 acc: {class0_acc*100:.1f}% (n={len(class0)})\n"
    f"class_1+ acc: {class1_acc*100:.1f}% (n={len(class1)})\n"
    f"Overall acc: {overall_acc*100:.1f}% (n={len(df)})"
)

plt.text(
    0.85,
    0.93,
    text,
    transform=plt.gca().transAxes,
    fontsize=11,
    verticalalignment="top",
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.9),
)

plt.title("WSI Model · class_0 vs class_1+ · Prediction Confidence")
plt.xlabel("Samples — sorted by P(class_1+) ascending")
plt.ylabel("P(class_1+)")
plt.ylim(0, 1)

plt.legend(loc="upper left")
plt.tight_layout()

plt.savefig("wsi_class0_vs_class1.png", dpi=200)
plt.show()