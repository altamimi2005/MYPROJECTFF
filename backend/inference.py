import os
from pathlib import Path
from typing import List
from io import BytesIO

import numpy as np
import tensorflow as tf
from PIL import Image
from tensorflow.keras.applications.efficientnet import preprocess_input


# ============================================================
# Configuration
# ============================================================

# IMPORTANT:
# Use the same image size that you used during training.
#
# EfficientNetB0 usually uses 224x224
# EfficientNetB3 usually uses 300x300
# EfficientNetB4 usually uses 380x380
#
# If your trained model was EfficientNetB0, keep this:


# If your model was EfficientNetB3, use:
IMG_SIZE = (300, 300)

# If your model was EfficientNetB4, use:
# IMG_SIZE = (380, 380)


BASE_DIR = Path(__file__).resolve().parent.parent

# Main model path in your GitHub repo root
MODEL_PATH = BASE_DIR / "best_model.keras"

# Optional second path, only if you later save another model inside outputs/
FALLBACK_MODEL_PATH = BASE_DIR / "outputs" / "solar_model_best.keras"

_model = None

# Keep this False first.
# Cropping can hurt accuracy if the model was not trained with cropped images.
ENABLE_AUTO_CROP = False


# ============================================================
# Model loading
# ============================================================

def load_model_once():
    """
    Load the model only once and reuse it for all requests.
    """
    global _model

    if _model is not None:
        return _model

    print("========== MODEL LOADING ==========")
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"MODEL_PATH: {MODEL_PATH}")
    print(f"FALLBACK_MODEL_PATH: {FALLBACK_MODEL_PATH}")

    if MODEL_PATH.exists():
        print(f"Loading model from: {MODEL_PATH}")
        _model = tf.keras.models.load_model(str(MODEL_PATH))
    elif FALLBACK_MODEL_PATH.exists():
        print(f"Main model missing. Loading fallback model from: {FALLBACK_MODEL_PATH}")
        _model = tf.keras.models.load_model(str(FALLBACK_MODEL_PATH))
    else:
        print("ERROR: No model file found.")
        print("Expected one of these:")
        print(f"1. {MODEL_PATH}")
        print(f"2. {FALLBACK_MODEL_PATH}")
        _model = None

    if _model is not None:
        print("Model loaded successfully.")
        print(f"Model input shape: {_model.input_shape}")
        print(f"Model output shape: {_model.output_shape}")

    print("===================================")

    return _model


# ============================================================
# Image preprocessing
# ============================================================

def preprocess_image(image_bytes: bytes, auto_crop: bool = False):
    """
    Convert uploaded image bytes into model-ready numpy array.

    Returns:
        final_array: shape (height, width, channels)
        crop_status: text description for frontend
    """

    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img_array = np.array(img)

    crop_status = "Not Applied"

    # Optional cropping. Disabled by default.
    if ENABLE_AUTO_CROP and auto_crop:
        try:
            from .cropper import crop_solar_panel
            img_array, crop_status = crop_solar_panel(img_array)
        except Exception as e:
            print(f"Warning: auto-cropping failed. Using original image. Error: {e}")
            crop_status = "Attempted — Failed"

    # Resize to model input size
    img_resized = Image.fromarray(img_array).resize(IMG_SIZE)

    # Convert to float32 numpy array
    final_array = np.array(img_resized, dtype=np.float32)

    # EfficientNet preprocessing
    # IMPORTANT:
    # Use this if your model was trained with EfficientNet preprocessing.
    # If your model was trained only with Rescaling(1./255), tell me,
    # because then this should be changed to final_array / 255.0
    final_array = preprocess_input(final_array)

    return final_array, crop_status


# ============================================================
# Prediction / batch processing
# ============================================================

def process_batch(
    image_bytes_list: List[bytes],
    filenames: List[str],
    auto_crop: bool = False
):
    """
    Process a batch of uploaded images.

    Expected binary sigmoid model output:
        pred close to 1 = Damaged
        pred close to 0 = Not Damaged

    If your results are reversed, switch the mapping in the section below.
    """

    model = load_model_once()

    if model is None:
        return [
            {
                "filename": f,
                "error": "Model not loaded. Check that best_model.keras exists in the project root.",
                "is_solar_panel": True,
                "original_index": i,
            }
            for i, f in enumerate(filenames)
        ]

    all_results = []
    valid_batch_arrays = []
    valid_indices = []
    crop_statuses = []

    # ------------------------------------------------------------
    # Preprocess images
    # ------------------------------------------------------------
    for i, (img_bytes, fname) in enumerate(zip(image_bytes_list, filenames)):
        try:
            img_array, crop_status = preprocess_image(
                img_bytes,
                auto_crop=auto_crop
            )

            valid_batch_arrays.append(img_array)
            valid_indices.append(i)
            crop_statuses.append(crop_status)

        except Exception as e:
            print(f"Error preprocessing {fname}: {e}")
            all_results.append(
                {
                    "filename": fname,
                    "error": f"Preprocessing failed: {str(e)}",
                    "is_solar_panel": False,
                    "original_index": i,
                }
            )

    if not valid_batch_arrays:
        all_results.sort(key=lambda x: x.get("original_index", 0))
        return all_results

    # Add batch dimension
    batch_tensor = np.stack(valid_batch_arrays, axis=0)

    print("========== INFERENCE DEBUG ==========")
    print(f"BATCH TENSOR SHAPE: {batch_tensor.shape}")
    print(f"BATCH TENSOR DTYPE: {batch_tensor.dtype}")
    print(f"BATCH TENSOR MIN: {np.min(batch_tensor)}")
    print(f"BATCH TENSOR MAX: {np.max(batch_tensor)}")
    print("=====================================")

    # ------------------------------------------------------------
    # Run prediction
    # ------------------------------------------------------------
    try:
        preds_raw = model.predict(batch_tensor, batch_size=32, verbose=0)

        print("========== RAW MODEL PREDICTIONS ==========")
        print(preds_raw[:10])
        print("===========================================")

        for j, original_idx in enumerate(valid_indices):
            fname = filenames[original_idx]

            raw_pred = preds_raw[j]

            # Handle different possible model outputs
            if np.ndim(raw_pred) == 0:
                pred = float(raw_pred)
            elif len(raw_pred) == 1:
                pred = float(raw_pred[0])
            else:
                # If model outputs two neurons like [not_damaged, damaged]
                damaged_probability = float(raw_pred[1])
                pred = damaged_probability

            # ====================================================
            # CLASS MAPPING
            # ====================================================
            # Current assumption:
            # pred close to 1 = Damaged
            # pred close to 0 = Not Damaged
            #
            # If the website gives reversed results, change the
            # mapping section below.
            # ====================================================

            if pred > 0.65:
                result_label = "Damaged"
                confidence = pred * 100
                is_damaged = True
                is_uncertain = False

            elif pred < 0.35:
                result_label = "Not Damaged"
                confidence = (1.0 - pred) * 100
                is_damaged = False
                is_uncertain = False

            else:
                result_label = "Uncertain"
                confidence = 50.0 + abs(pred - 0.5) * 100
                is_damaged = pred > 0.5
                is_uncertain = True

            all_results.append(
                {
                    "filename": fname,
                    "result": result_label,
                    "confidence": round(float(confidence), 2),
                    "raw_score": round(float(pred), 4),
                    "is_solar_panel": True,
                    "is_damaged": is_damaged,
                    "is_uncertain": is_uncertain,
                    "crop_status": crop_statuses[j],
                    "original_index": original_idx,
                    "image_data": image_bytes_list[original_idx],
                }
            )

    except Exception as e:
        print(f"Prediction failed: {e}")

        for original_idx in valid_indices:
            all_results.append(
                {
                    "filename": filenames[original_idx],
                    "error": f"Prediction failed: {str(e)}",
                    "is_solar_panel": False,
                    "original_index": original_idx,
                }
            )

    all_results.sort(key=lambda x: x.get("original_index", 0))
    return all_results
