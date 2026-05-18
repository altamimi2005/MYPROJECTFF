
import os
from pathlib import Path
import hashlib
from PIL import Image
import io

def get_image_hash(path):
    try:
        with Image.open(path) as img:
            # Resize to small to catch near-duplicates too
            img = img.resize((32, 32)).convert("L")
            return hashlib.md5(img.tobytes()).hexdigest()
    except:
        return None

data_dir = Path(r"C:\Users\qafms\OneDrive\Desktop\Data Set\Data Set")
categories = ["DAMAGED", "NOT_DAMAGED"]

hashes = {}
duplicates = []
conflicts = []

print("Scanning for duplicate/conflicting images...")

for cat in categories:
    cat_path = data_dir / cat
    for img_path in cat_path.rglob("*"):
        if img_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
            h = get_image_hash(img_path)
            if h:
                if h in hashes:
                    if hashes[h]["category"] != cat:
                        conflicts.append((str(img_path), hashes[h]["path"]))
                    else:
                        duplicates.append((str(img_path), hashes[h]["path"]))
                else:
                    hashes[h] = {"category": cat, "path": str(img_path)}

print(f"Found {len(duplicates)} duplicates.")
print(f"Found {len(conflicts)} CONFLICTING images (same image, different labels!).")

if conflicts:
    print("\n--- CONFLICTS DETECTED ---")
    for c in conflicts[:10]:
        print(f"Conflict: {c[0]} vs {c[1]}")
    
    # Save conflicts to a file for pruning
    with open("data_conflicts.txt", "w") as f:
        for c in conflicts:
            f.write(f"{c[0]}|{c[1]}\n")
else:
    print("No conflicting labels found! Dataset is clean.")
