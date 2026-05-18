import os
from LOAD import get_datasets, DATA_DIR

print(f"Directory: {DATA_DIR}")
if not DATA_DIR.exists():
    print("Directory does not exist!")
else:
    total_files = 0
    for d in DATA_DIR.iterdir():
        if d.is_dir():
            count = sum(1 for _ in d.rglob("*.*"))
            print(f"Folder '{d.name}': {count} images")
            total_files += count
    print(f"Total raw images: {total_files}\n")

try:
    print("--- DATASET PIPELINE ---")
    _, _, _, info = get_datasets()
    print(info)
except Exception as e:
    print(f"Error checking dataset: {e}")
