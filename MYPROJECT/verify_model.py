
import tensorflow as tf
import os

model_path = r"c:\Users\qafms\OneDrive\Desktop\MYPROJECT\MYPROJECT\best_model.keras"

if not os.path.exists(model_path):
    print(f"Error: {model_path} does not exist.")
else:
    try:
        model = tf.keras.models.load_model(model_path)
        print("Model loaded successfully!")
        model.summary()
        
        # Verify output shape and classes
        print("\nInput shape:", model.input_shape)
        print("Output shape:", model.output_shape)
        
        # Final move to outputs folder
        os.makedirs("outputs", exist_ok=True)
        final_path = os.path.join("outputs", "solar_crack_model_v1.keras")
        import shutil
        shutil.copy(model_path, final_path)
        print(f"\n✅ Verified and copied to: {final_path}")
        
    except Exception as e:
        print(f"Error loading model: {e}")
