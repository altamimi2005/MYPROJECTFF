from pathlib import Path
import tensorflow as tf
import numpy as np
from sklearn.model_selection import train_test_split

# ===== CONFIG =====
DATA_DIR = Path(r"C:\Users\qafms\OneDrive\Desktop\Data Set\Data Set")
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
SEED = 42

VALID_EXT = {".jpg", ".jpeg", ".png"}

# ===== IMAGE LOAD =====
def _decode_resize(path, label):
    img = tf.io.read_file(path)
    img = tf.image.decode_image(img, channels=3, expand_animations=False)
    img = tf.image.resize(img, IMG_SIZE)
    img = tf.cast(img, tf.float32)
    return img, tf.cast(label, tf.float32)

# ===== DATASET CREATION =====
def _make_ds(paths, labels, shuffle=False):
    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    
    if shuffle:
        ds = ds.shuffle(buffer_size=len(paths), seed=SEED)
    
    ds = ds.map(_decode_resize, num_parallel_calls=tf.data.AUTOTUNE)
    ds = ds.cache()  # <--- MAGICAL SPEEDUP: Stores dataset in RAM after epoch 1
    ds = ds.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)
    
    return ds

# ===== MAIN FUNCTION =====
def get_datasets():
    paths = []
    labels = []

    if not DATA_DIR.exists():
        raise ValueError(f"Data directory not found: {DATA_DIR}")

    for folder in DATA_DIR.iterdir():
        if not folder.is_dir():
            continue

        name = folder.name.lower()

        # ===== STRICT LABELING =====
        if name == "not_damaged":
            label = 0
        elif name == "damaged":
            label = 1
        else:
            continue   # Ignore any other folders

        for p in folder.rglob("*"):
            if p.suffix.lower() in VALID_EXT:
                paths.append(str(p))
                labels.append(label)

    # ===== SAFETY CHECK =====
    if len(paths) == 0:
        raise ValueError("No images found. Check dataset path and folder names.")

    print("Total images:", len(paths))
    print("Class balance (0: Not Damaged, 1: Damaged):", np.bincount(labels))

    # ===== SPLIT (70/15/15) =====
    X_train, X_temp, y_train, y_temp = train_test_split(
        paths, labels,
        test_size=0.3,
        random_state=SEED,
        stratify=labels
    )

    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp,
        test_size=0.5,
        random_state=SEED,
        stratify=y_temp
    )

    # ===== DATASETS =====
    train_ds = _make_ds(X_train, y_train, shuffle=True)
    val_ds = _make_ds(X_val, y_val)
    test_ds = _make_ds(X_test, y_test)

    info = {
        "total": len(paths),
        "train": len(X_train),
        "val": len(X_val),
        "test": len(X_test),
        "balance": np.bincount(labels).tolist()
    }

    return train_ds, val_ds, test_ds, info
