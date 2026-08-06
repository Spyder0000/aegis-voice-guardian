import csv
import io
import json
import os
import urllib.request

# Download metadata CSV and fetch clips directly without Hugging Face 'datasets' or 'torchcodec' dependencies
METADATA_URL = "https://huggingface.co/datasets/intronhealth/afrispeech-dialog/raw/main/metadata.csv"
RAW_BASE_URL = "https://huggingface.co/datasets/intronhealth/afrispeech-dialog/resolve/main"

os.makedirs("afriswitch_clips", exist_ok=True)

print("Fetching metadata from Hugging Face...")
req = urllib.request.urlopen(METADATA_URL)
content = req.read().decode("utf-8")

reader = csv.DictReader(io.StringIO(content))
test_set_entries = []

for i, row in enumerate(reader):
    if i >= 15:
        break

    file_name = row["file_name"]
    transcript = row["transcript"]
    audio_url = f"{RAW_BASE_URL}/{file_name}"
    save_path = f"afriswitch_clips/clip_{i}.wav"

    print(f"Downloading clip_{i}.wav ({i+1}/15)...")
    urllib.request.urlretrieve(audio_url, save_path)
    print(f"clip_{i}: {transcript[:70]}...")

    test_set_entries.append({
        "id": f"clip_{i}",
        "audio_path": save_path,
        "ground_truth": transcript,
        "is_code_switched": True,
        "accent": row.get("accent", ""),
        "country": row.get("country", "")
    })

# Save asr_test_set.json
test_set_path = "ml/data/synthetic/asr_test_set.json"
with open(test_set_path, "w", encoding="utf-8") as f:
    json.dump(test_set_entries, f, indent=2)

print(f"\nSuccessfully downloaded 15 clips to 'afriswitch_clips/'!")
print(f"Saved benchmark test set metadata to '{test_set_path}'")

