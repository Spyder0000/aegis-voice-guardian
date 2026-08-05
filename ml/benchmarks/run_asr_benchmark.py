"""
Benchmark harness: measures ASR quality + downstream risk-detection quality.
Owner: Toluwalase Ajiboye

Run against Darius's synthetic scam/genuine call sets.
"""
import json
import sys
from pathlib import Path

# Ensure root directory is in sys.path when running script directly
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.trust_score.rule_based import score


def word_error_rate(reference: str, hypothesis: str) -> float:
    """Basic WER via edit distance on word sequences."""
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()
    m, n = len(ref_words), len(hyp_words)
    if m == 0:
        return 0.0 if n == 0 else 1.0

    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[m][n] / m


def run_intervention_benchmark(labeled_calls: list[dict]) -> dict:
    """
    labeled_calls: [{"transcript": ..., "features": ..., "is_scam": bool}, ...]
    Returns false-positive rate, false-negative rate, and per-call results.
    """
    results = []
    false_positives = 0  # genuine flagged as risky (MEDIUM/HIGH)
    false_negatives = 0  # scam not flagged as risky (LOW)
    total_genuine = 0
    total_scam = 0

    for call in labeled_calls:
        transcript = call.get("transcript")
        features = call.get("features", {})
        is_scam = call.get("is_scam", False)

        result = score(features, transcript=transcript)
        flagged = result["risk_level"] in ("MEDIUM", "HIGH")

        if is_scam:
            total_scam += 1
            if not flagged:
                false_negatives += 1
        else:
            total_genuine += 1
            if flagged:
                false_positives += 1

        results.append({
            "id": call.get("id"),
            "is_scam": is_scam,
            "risk_level": result["risk_level"],
            "score": result["score"],
            "reasons": result["reasons"],
            "flagged": flagged,
        })

    total = len(labeled_calls)
    fp_rate = false_positives / total_genuine if total_genuine > 0 else (false_positives / total if total else 0.0)
    fn_rate = false_negatives / total_scam if total_scam > 0 else (false_negatives / total if total else 0.0)

    return {
        "total_calls": total,
        "total_genuine": total_genuine,
        "total_scams": total_scam,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "false_positive_rate": round(fp_rate, 4),
        "false_negative_rate": round(fn_rate, 4),
        "per_call_results": results,
    }


if __name__ == "__main__":
    data_path = ROOT_DIR / "ml" / "data" / "synthetic" / "labeled_calls.json"
    if not data_path.exists():
        print(
            "Benchmark harness is blocked on Darius's synthetic data generation. "
            f"Expected file at: {data_path}"
        )
    else:
        labeled_calls = json.loads(data_path.read_text(encoding="utf-8"))
        benchmark_results = run_intervention_benchmark(labeled_calls)
        print(json.dumps(benchmark_results, indent=2))
