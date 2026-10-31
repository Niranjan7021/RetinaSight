
from pathlib import Path
import copy
import json
import random

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from PIL import Image
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix
)

# ---------------- CONFIGURATION ----------------

DATA_DIR = Path(r"C:\retina-data")
IMAGE_DIR = DATA_DIR / "train_images"
CSV_FILE = DATA_DIR / "train.csv"

PROJECT_DIR = Path(__file__).resolve().parent
MODEL_DIR = PROJECT_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_FILE = MODEL_DIR / "dr_model.pth"

IMAGE_SIZE = 224
BATCH_SIZE = 16
EPOCHS = 8
LEARNING_RATE = 0.0001
SEED = 42

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

# ---------------- CHECK DATASET ----------------

if not IMAGE_DIR.exists():
    raise FileNotFoundError(f"Image folder not found: {IMAGE_DIR}")

if not CSV_FILE.exists():
    raise FileNotFoundError(f"CSV file not found: {CSV_FILE}")

df = pd.read_csv(CSV_FILE)

required_columns = {"id_code", "diagnosis"}
if not required_columns.issubset(df.columns):
    raise ValueError("train.csv must contain id_code and diagnosis columns.")

df["diagnosis"] = df["diagnosis"].astype(int)

def find_image(image_id):
    for ext in (".png", ".jpg", ".jpeg", ".tif", ".tiff"):
        path = IMAGE_DIR / f"{image_id}{ext}"
        if path.exists():
            return path
    return None

df["image_path"] = df["id_code"].apply(find_image)
missing = df["image_path"].isna().sum()

if missing:
    print(f"Warning: {missing} images were not found and will be skipped.")
    df = df.dropna(subset=["image_path"]).copy()

if df.empty:
    raise RuntimeError("No images found. Check IMAGE_DIR and image filenames.")

if not set(df["diagnosis"].unique()).issubset({0, 1, 2, 3, 4}):
    raise ValueError("Expected retinal grades from 0 to 4.")

print(f"Images found: {len(df)}")
print("Class distribution:")
print(df["diagnosis"].value_counts().sort_index())
print("Training device:", DEVICE)

# ---------------- TRAIN / VALIDATION SPLIT ----------------

train_df, val_df = train_test_split(
    df,
    test_size=0.20,
    random_state=SEED,
    stratify=df["diagnosis"]
)

print(f"Training images: {len(train_df)}")
print(f"Validation images: {len(val_df)}")

# ---------------- IMAGE TRANSFORMS ----------------

train_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

val_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# ---------------- DATASET ----------------

class RetinaDataset(Dataset):
    def __init__(self, dataframe, transform):
        self.data = dataframe.reset_index(drop=True)
        self.transform = transform

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        row = self.data.iloc[index]

        with Image.open(row["image_path"]) as image:
            image = image.convert("RGB")
            image = self.transform(image)

        label = int(row["diagnosis"])
        return image, label


train_dataset = RetinaDataset(train_df, train_transform)
val_dataset = RetinaDataset(val_df, val_transform)

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0,
    pin_memory=torch.cuda.is_available()
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0,
    pin_memory=torch.cuda.is_available()
)

# ---------------- CNN MODEL ----------------

print("Loading pretrained ResNet18...")

weights = models.ResNet18_Weights.DEFAULT
model = models.resnet18(weights=weights)

# Replace the final layer for five retinal grades.
model.fc = nn.Linear(model.fc.in_features, 5)
model = model.to(DEVICE)

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LEARNING_RATE
)

# ---------------- TRAINING ----------------

best_f1 = -1.0
best_state = None

for epoch in range(EPOCHS):
    model.train()
    train_loss = 0.0
    train_correct = 0
    train_total = 0

    for images, labels in train_loader:
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)

        optimizer.zero_grad(set_to_none=True)

        outputs = model(images)
        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        train_loss += loss.item() * images.size(0)
        train_correct += (outputs.argmax(1) == labels).sum().item()
        train_total += labels.size(0)

    model.eval()
    val_true = []
    val_pred = []
    val_loss = 0.0

    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(DEVICE)
            labels = labels.to(DEVICE)

            outputs = model(images)
            loss = criterion(outputs, labels)

            val_loss += loss.item() * images.size(0)
            predictions = outputs.argmax(1)

            val_true.extend(labels.cpu().tolist())
            val_pred.extend(predictions.cpu().tolist())

    train_accuracy = train_correct / train_total
    val_accuracy = accuracy_score(val_true, val_pred)
    val_macro_f1 = f1_score(
        val_true,
        val_pred,
        labels=[0, 1, 2, 3, 4],
        average="macro",
        zero_division=0
    )

    print(f"\nEpoch {epoch + 1}/{EPOCHS}")
    print(f"Train loss: {train_loss / train_total:.4f}")
    print(f"Train accuracy: {train_accuracy:.4f}")
    print(f"Validation loss: {val_loss / len(val_dataset):.4f}")
    print(f"Validation accuracy: {val_accuracy:.4f}")
    print(f"Validation macro F1: {val_macro_f1:.4f}")

    if val_macro_f1 > best_f1:
        best_f1 = val_macro_f1
        best_state = copy.deepcopy(model.state_dict())

        torch.save({
            "model_state_dict": best_state,
            "num_classes": 5,
            "image_size": IMAGE_SIZE,
            "class_names": [
                "No DR",
                "Mild",
                "Moderate",
                "Severe",
                "Proliferative DR"
            ]
        }, MODEL_FILE)

        print("Best model saved.")

# ---------------- FINAL EVALUATION ----------------

if best_state is None:
    raise RuntimeError("Training did not produce a saved model.")

model.load_state_dict(best_state)
model.eval()

val_true = []
val_pred = []

with torch.no_grad():
    for images, labels in val_loader:
        images = images.to(DEVICE)
        predictions = model(images).argmax(1)

        val_true.extend(labels.tolist())
        val_pred.extend(predictions.cpu().tolist())

print("\nFinal validation accuracy:",
      round(accuracy_score(val_true, val_pred), 4))

print("\nClassification report:")
print(classification_report(
    val_true,
    val_pred,
    labels=[0, 1, 2, 3, 4],
    target_names=[
        "No DR", "Mild", "Moderate", "Severe", "Proliferative DR"
    ],
    zero_division=0
))

print("Confusion matrix:")
print(confusion_matrix(val_true, val_pred, labels=[0, 1, 2, 3, 4]))

metrics = {
    "validation_accuracy": float(accuracy_score(val_true, val_pred)),
    "validation_macro_f1": float(f1_score(
        val_true, val_pred,
        labels=[0, 1, 2, 3, 4],
        average="macro",
        zero_division=0
    )),
    "best_model": str(MODEL_FILE)
}

with open(MODEL_DIR / "metrics.json", "w", encoding="utf-8") as file:
    json.dump(metrics, file, indent=2)

print(f"\nTraining complete. Model saved to:\n{MODEL_FILE}")
print("Metrics saved to:", MODEL_DIR / "metrics.json")
