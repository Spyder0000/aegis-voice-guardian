"""
ml/benchmarks/diagnose_false_positives.py
Owner: Toluwalase Ajiboye

One-off diagnostic: isolates exactly which genuine calls got wrongly flagged,
and why, so weight-tuning is based on evidence instead of guessing.
"""
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.benchmarks.run_asr_benchmark import run_intervention_benchmark

data_path = ROOT_DIR / "ml" / "data" / "synthetic" / "labeled_calls.json"
labeled_calls = json.loads(data_path.read_text())
result = run_intervention_benchmark(labeled_calls)

false_positives = [
    r for r in result["per_call_results"]
    if r["flagged"] and not r["is_scam"]
]

print(f"Found {len(false_positives)} false positives:\n")
for fp in false_positives:
    print(json.dumps(fp, indent=2))
    print("-" * 40)
