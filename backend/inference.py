import os
from pathlib import Path
from typing import List
import numpy as np
import tensorflow as tf
from PIL import Image
from io import BytesIO

# Suppress warnings
os.environ["KERAS_BACKEND"] = "tensorflow"
import keras

# Import EfficientNet preprocessing
from tensorflow.keras.applications.efficientnet import preprocess_input

IMG_SIZE = (224, 224)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Single Model Path (Using newly trained model)
MODEL_PATH = Path(os.path.join(BASE_DIR, "outputs", "solar_model_best.keras"))
FALLBACK_PATH = Path(os.path.join(BASE_DIR, "best_model.keras"))

_model = None

def load_models():
    global _model
    if _model is None:
        if MODEL_PATH.exists():
            print(f"Loading V2 Model from {MODEL_PATH}")
            _model = keras.models.load_model(str(MODEL_PATH))
        elif FALLBACK_PATH.exists():
            print(f"V2 missing. Using V1 from {FALLBACK_PATH}")
            _model = keras.models.load_model(str(FALLBACK_PATH))
        else:
            print("WARNING: No models found. Please train the model first.")

# Feature Toggle for OpenCV Auto-Cropping (Set to False to disable and return to original performance)
ENABLE_AUTO_CROP = True

def preprocess_image(image_bytes: bytes, auto_crop: bool = True):
    """
    Standard preprocessing for a single image with optional auto-cropping.
    Returns (float32 numpy array, crop_status string).
    """
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img_array = np.array(img)
    crop_status = "Not Needed"
    
    # NEW: Mathematically find and crop the solar panel before it gets resized
    if ENABLE_AUTO_CROP and auto_crop:
        try:
            from .cropper import crop_solar_panel
            img_array, crop_status = crop_solar_panel(img_array)
        except Exception as e:
            print(f"Warning: Cropping failed, using raw image. {e}")
            crop_status = "Attempted — Failed"
            
    # Resize the (potentially cropped) image for the model
    img_cropped = Image.fromarray(img_array)
    img_cropped = img_cropped.resize(IMG_SIZE)
    final_array = np.array(img_cropped, dtype=np.float32)
    return final_array, crop_status

def process_batch(image_bytes_list: List[bytes], filenames: List[str], auto_crop: bool = True):
    """
    Optimized batched processing. 
    New Mapping: 0 = NOT_DAMAGED, 1 = DAMAGED
    """
    load_models()
    
    if _model is None:
        return [{"filename": f, "error": "Model not loaded.", "is_solar_panel": True} for f in filenames]

    all_results = []
    valid_batch_arrays = []
    valid_indices = []
    cropped_flags = []

    # 1. Preprocessing
    for i, (img_bytes, fname) in enumerate(zip(image_bytes_list, filenames)):
        try:
            img_array, crop_status = preprocess_image(img_bytes, auto_crop=auto_crop)
            valid_batch_arrays.append(img_array)
            valid_indices.append(i)
            cropped_flags.append(crop_status)
        except Exception as e:
            all_results.append({
                "filename": fname, "error": str(e), "is_solar_panel": False, "original_index": i
            })

    if not valid_batch_arrays:
        return all_results

    # 🚀 Batched Inference
    batch_tensor = np.stack(valid_batch_arrays, axis=0)
    
    try:
        preds_raw = _model.predict(batch_tensor, batch_size=32, verbose=0)
        
        for i, idx in enumerate(valid_indices):
            pred = float(preds_raw[i][0])
            fname = filenames[idx]
            
            # ✅ CORRECT MAPPING: 1 = Damaged, 0 = Safe
            if pred > 0.65:
                # Confidently Damaged
                res_label = "Damaged"
                conf = pred * 100
                is_damaged = True
                is_uncertain = False
            elif pred < 0.35:
                # Confidently Not Damaged
                res_label = "Not Damaged"
                conf = (1.0 - pred) * 100
                is_damaged = False
                is_uncertain = False
            else:
                # Uncertain - No longer calling it 'Not a solar panel' or 'Uncertain / Review'
                res_label = "Uncertain"
                conf = 50.0 + abs(pred - 0.5) * 100
                is_damaged = (pred > 0.5)
                is_uncertain = True
                
            all_results.append({
                "filename": fname,
                "result": res_label,
                "confidence": round(float(conf), 2),
                "raw_score": round(float(pred), 4),
                "is_solar_panel": True, # Assume it's solar for now
                "is_damaged": is_damaged,
                "is_uncertain": is_uncertain,
                "crop_status": cropped_flags[i],
                "original_index": idx,
                "image_data": image_bytes_list[idx] 
            })
    except Exception as e:
        for idx in valid_indices:
            all_results.append({"filename": filenames[idx], "error": str(e), "is_solar_panel": False, "original_index": idx})

    all_results.sort(key=lambda x: x.get("original_index", 0))
    return all_results
