import tensorflow as tf
from LOAD import get_datasets

print("Loading model...")
model = tf.keras.models.load_model("best_model.keras")

print("Loading dataset...")
train_ds, val_ds, test_ds, info = get_datasets()

print("Evaluating on Test Dataset...")
results = model.evaluate(test_ds)

metrics = dict(zip(model.metrics_names, results))
print("\n--- MODEL PERFORMANCE ---")
for k, v in metrics.items():
    print(f"{k}: {v:.4f}")
