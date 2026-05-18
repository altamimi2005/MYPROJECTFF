import os
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np
from LOAD import get_datasets, IMG_SIZE

# Ensure reproducible logic
tf.keras.utils.set_random_seed(42)

# Enable Mixed Precision for faster training on modern GPUs
tf.keras.mixed_precision.set_global_policy('mixed_float16')

def build_model():
    # ===== AUGMENTATION (IMPROVED BUT SAFE) =====
    augment = tf.keras.Sequential([
        tf.keras.layers.RandomFlip("horizontal"),
        tf.keras.layers.RandomRotation(0.05),
        tf.keras.layers.RandomZoom(0.1),
        tf.keras.layers.RandomContrast(0.1),
    ], name="augment")

    # ===== BASE MODEL =====
    base = tf.keras.applications.EfficientNetB3(
        include_top=False,
        weights="imagenet",
        input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3),
    )
    base.trainable = False

    # ===== MODEL =====
    inputs = tf.keras.Input(shape=(IMG_SIZE[0], IMG_SIZE[1], 3))
    x = augment(inputs)
    x = tf.keras.applications.efficientnet.preprocess_input(x)

    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.BatchNormalization()(x)

    # 👉 IMPORTANT (this is what made your model strong)
    x = tf.keras.layers.Dense(128, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.3)(x)

    # When using mixed precision, the output layer must be float32 for numerical stability
    outputs = tf.keras.layers.Dense(1, activation="sigmoid", dtype="float32")(x)

    model = tf.keras.Model(inputs, outputs)
    return model, base

def train():
    # ===== LOAD DATA =====
    print("Loading datasets...")
    train_ds, val_ds, test_ds, info = get_datasets()
    print(f"Dataset Info: {info}")

    model, base = build_model()

    # ===== COMPILE =====
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=3e-4),
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
        ],
    )

    # ===== TRAIN STAGE 1 =====
    print("\n--- STAGE 1: FEATURE EXTRACTION ---")
    model.fit(train_ds, validation_data=val_ds, epochs=10)

    # ===== FINE-TUNE =====
    print("\n--- STAGE 2: FINE-TUNING ---")
    base.trainable = True
    for layer in base.layers[:-50]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
        loss="binary_crossentropy",
        metrics=["accuracy", "precision", "recall"]
    )

    # Using ModelCheckpoint to save the actual best file
    checkpoint = tf.keras.callbacks.ModelCheckpoint(
        "best_model.keras", 
        monitor="val_accuracy", 
        save_best_only=True
    )

    model.fit(train_ds, validation_data=val_ds, epochs=8, callbacks=[checkpoint])

    # ===== TEST & EVALUATION =====
    print("\n--- FINAL EVALUATION ---")
    model.evaluate(test_ds)
    
    y_true, y_pred = [], []
    for images, labels in test_ds:
        preds = model.predict(images, verbose=0)
        y_true.extend(labels.numpy().astype(int).reshape(-1))
        y_pred.extend((preds > 0.5).astype(int).reshape(-1))
        
    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, target_names=["Not Damaged", "Damaged"]))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_true, y_pred))

    # Also save the final state just in case
    model.save("best_model.keras")
    print(f"✅ Saved Best Model to: best_model.keras")

if __name__ == "__main__":
    train()
