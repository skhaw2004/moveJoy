"""
MoveJoy v2 — Gesture Classifier Training
------------------------------------------
Trains a small neural network on collected YOLO keypoints.
Input:  51 values (17 keypoints × x, y, confidence)
Output: 4 classes (up, left, right, idle)

Saves trained model to: gesture_model.keras
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
from tensorflow import keras

# ── Config ───────────────────────────────────────────────────────────────────
INPUT_CSV   = 'gesture_data.csv'
OUTPUT_MODEL = 'gesture_model.keras'
EPOCHS      = 50
BATCH_SIZE  = 32
# ─────────────────────────────────────────────────────────────────────────────

print("=== MOVEJOY v2 — GESTURE MODEL TRAINING ===\n")

# Load data
print("Loading data...")
df = pd.read_csv(INPUT_CSV)
X = df.drop('label', axis=1).values.astype(np.float32)
y = df['label'].values

print(f"Samples: {len(y)}")
print(f"Classes: {np.unique(y)}")
print(f"Input shape: {X.shape[1]} features\n")

# Encode labels
encoder = LabelEncoder()
y_encoded = encoder.fit_transform(y)
y_onehot  = keras.utils.to_categorical(y_encoded)
num_classes = len(encoder.classes_)

print(f"Label mapping:")
for i, label in enumerate(encoder.classes_):
    print(f"  {i} → {label}")
print()

# Train / validation split
X_train, X_val, y_train, y_val = train_test_split(
    X, y_onehot, test_size=0.2, random_state=42, stratify=y_encoded
)
print(f"Training samples:   {len(X_train)}")
print(f"Validation samples: {len(X_val)}\n")

# Build model
model = keras.Sequential([
    keras.layers.Input(shape=(X.shape[1],)),
    keras.layers.Dense(128, activation='relu'),
    keras.layers.Dropout(0.3),
    keras.layers.Dense(64, activation='relu'),
    keras.layers.Dropout(0.2),
    keras.layers.Dense(32, activation='relu'),
    keras.layers.Dense(num_classes, activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

model.summary()
print()

# Train
print("Training...\n")
history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    verbose=1
)

# Evaluate
val_loss, val_acc = model.evaluate(X_val, y_val, verbose=0)
print(f"\nValidation accuracy: {val_acc * 100:.1f}%")

# Save model
model.save(OUTPUT_MODEL)
print(f"Model saved to: {OUTPUT_MODEL}")

# Save label mapping
import json
label_map = {str(i): label for i, label in enumerate(encoder.classes_)}
with open('gesture_labels.json', 'w') as f:
    json.dump(label_map, f, indent=2)
print(f"Labels saved to: gesture_labels.json")

print("\n=== TRAINING COMPLETE ===")
