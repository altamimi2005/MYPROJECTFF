
from pathlib import Path
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight

# ====== CHANGE THIS ONLY ======
DATA_DIR = Path(r"C:\Users\qafms\OneDrive\Desktop\Data Set\Data Set")  # contains DAMAGED/ and NOT_DAMAGED/

# ====== DATA LOADING SETTINGS ======
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
SEED = 42
VAL_SIZE = 0.15
TEST_SIZE = 0.15
EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def _scan_dataset(data_dir: Path):
    if not data_dir.exists():
        raise FileNotFoundError(f"Dataset folder not found: {data_dir}")

    # Hardcode order to ensure 0 = NOT_DAMAGED, 1 = DAMAGED
    class_names = ["NOT_DAMAGED", "DAMAGED"]
    class_to_idx = {name: i for i, name in enumerate(class_names)}

    paths, labels = [], []
    for cls in class_names:
        for p in (data_dir / cls).rglob("*"):
            if p.suffix.lower() in EXTS:
                paths.append(str(p))
                labels.append(class_to_idx[cls])

    if len(paths) == 0:
        raise ValueError("No images found. Check dataset folder structure and file extensions.")

    return np.array(paths), np.array(labels, dtype=np.int32), class_names


def _decode_resize(path, label):
    img_bytes = tf.io.read_file(path)
    img = tf.image.decode_image(img_bytes, channels=3, expand_animations=False)
    img = tf.image.resize(img, IMG_SIZE)
    img = tf.cast(img, tf.float32)  # normalization happens in MODEL.py
    return img, tf.cast(label, tf.float32)


# ===== AUGMENTATION FUNCTIONS =====
def _augment_standard(image, label):
    """Standard augmentation for the majority class (DAMAGED).
    Moderate transforms that add variety without over-distorting."""
    image = tf.image.random_flip_left_right(image)
    image = tf.image.random_brightness(image, max_delta=0.1)
    image = tf.image.random_contrast(image, lower=0.9, upper=1.1)
    image = tf.clip_by_value(image, 0.0, 255.0)
    return image, label


def _augment_aggressive(image, label):
    """Aggressive but realistic augmentation for minority class (NOT_DAMAGED).
    Stronger transforms to synthetically expand the smaller class."""
    image = tf.image.random_flip_left_right(image)
    image = tf.image.random_flip_up_down(image)
    image = tf.image.random_brightness(image, max_delta=0.2)
    image = tf.image.random_contrast(image, lower=0.75, upper=1.25)
    image = tf.image.random_saturation(image, lower=0.7, upper=1.3)
    image = tf.image.random_hue(image, max_delta=0.04)
    # Random zoom via crop and resize
    crop_factor = tf.random.uniform([], minval=0.8, maxval=1.0)
    crop_h = tf.cast(tf.cast(IMG_SIZE[0], tf.float32) * crop_factor, tf.int32)
    crop_w = tf.cast(tf.cast(IMG_SIZE[1], tf.float32) * crop_factor, tf.int32)
    image = tf.image.random_crop(image, [crop_h, crop_w, 3])
    image = tf.image.resize(image, IMG_SIZE)
    image = tf.clip_by_value(image, 0.0, 255.0)
    return image, label


def _make_ds(paths, labels, shuffle=False):
    """Standard dataset builder (used for val/test - NO augmentation)."""
    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    if shuffle:
        ds = ds.shuffle(buffer_size=len(paths), seed=SEED, reshuffle_each_iteration=True)
    ds = ds.map(_decode_resize, num_parallel_calls=tf.data.AUTOTUNE)
    ds = ds.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)
    return ds


def _make_balanced_train_ds(paths, labels):
    """Creates balanced training batches with class-conditional augmentation.
    - Oversamples the minority class (NOT_DAMAGED, label=0)
    - Applies aggressive augmentation to minority, standard to majority
    - Uses sample_from_datasets for 50/50 balanced batches"""

    # Separate by class
    class_0_mask = labels == 0  # NOT_DAMAGED (minority)
    class_1_mask = labels == 1  # DAMAGED (majority)

    paths_0, labels_0 = paths[class_0_mask], labels[class_0_mask]
    paths_1, labels_1 = paths[class_1_mask], labels[class_1_mask]

    print(f"  Balanced batching: class 0 (NOT_DAMAGED): {len(paths_0)}, class 1 (DAMAGED): {len(paths_1)}")

    # Class 0 (minority) — aggressive augmentation + repeat to oversample
    ds_0 = tf.data.Dataset.from_tensor_slices((paths_0, labels_0))
    ds_0 = ds_0.shuffle(len(paths_0), seed=SEED, reshuffle_each_iteration=True)
    ds_0 = ds_0.repeat()  # repeat minority to balance
    ds_0 = ds_0.map(_decode_resize, num_parallel_calls=tf.data.AUTOTUNE)
    ds_0 = ds_0.map(_augment_aggressive, num_parallel_calls=tf.data.AUTOTUNE)

    # Class 1 (majority) — standard augmentation + repeat for infinite sampling
    ds_1 = tf.data.Dataset.from_tensor_slices((paths_1, labels_1))
    ds_1 = ds_1.shuffle(len(paths_1), seed=SEED, reshuffle_each_iteration=True)
    ds_1 = ds_1.repeat()
    ds_1 = ds_1.map(_decode_resize, num_parallel_calls=tf.data.AUTOTUNE)
    ds_1 = ds_1.map(_augment_standard, num_parallel_calls=tf.data.AUTOTUNE)

    # 50/50 balanced sampling
    balanced_ds = tf.data.Dataset.sample_from_datasets(
        [ds_0, ds_1], weights=[0.5, 0.5], seed=SEED
    )

    # Steps per epoch: see all majority-class images + equal number of minority
    steps_per_epoch = (2 * len(paths_1)) // BATCH_SIZE

    balanced_ds = balanced_ds.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)

    return balanced_ds, steps_per_epoch


def get_datasets():
    """
    Returns:
      train_ds, val_ds, test_ds, class_names, info_dict
    """
    paths, labels, class_names = _scan_dataset(DATA_DIR)

    temp_size = VAL_SIZE + TEST_SIZE
    X_train, X_temp, y_train, y_temp = train_test_split(
        paths, labels,
        test_size=temp_size,
        random_state=SEED,
        stratify=labels
    )

    val_ratio_in_temp = VAL_SIZE / temp_size
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp,
        test_size=(1 - val_ratio_in_temp),
        random_state=SEED,
        stratify=y_temp
    )

    # ===== BALANCED TRAINING DATASET =====
    train_ds, steps_per_epoch = _make_balanced_train_ds(X_train, y_train)

    # ===== VAL / TEST (no augmentation, no balancing) =====
    val_ds = _make_ds(X_val, y_val, shuffle=False)
    test_ds = _make_ds(X_test, y_test, shuffle=False)

    # ===== CLASS WEIGHTS (extra safety net for the loss function) =====
    cw = compute_class_weight("balanced", classes=np.unique(y_train), y=y_train)
    class_weight = {i: float(w) for i, w in enumerate(cw)}

    info = {
        "total": int(len(paths)),
        "train": int(len(X_train)),
        "val": int(len(X_val)),
        "test": int(len(X_test)),
        "class_names": class_names,
        "train_class_balance": np.bincount(y_train).tolist(),
        "val_class_balance": np.bincount(y_val).tolist(),
        "test_class_balance": np.bincount(y_test).tolist(),
        "class_weight": class_weight,
        "steps_per_epoch": steps_per_epoch,
    }

    return train_ds, val_ds, test_ds, class_names, info


# Optional quick test (still "loading", not model)
if __name__ == "__main__":
    train_ds, val_ds, test_ds, class_names, info = get_datasets()
    print("Classes:", class_names)
    print("Info:", info)
    for x, y in train_ds.take(1):
        print("X batch:", x.shape)
        print("y batch:", y.shape)
