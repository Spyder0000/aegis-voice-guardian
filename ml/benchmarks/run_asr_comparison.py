"""
ml/benchmarks/run_asr_comparison.py
Owner: Toluwalase Ajiboye

THE ACTUAL CHALLENGE REQUIREMENT: benchmark performance on code-switched
AUDIO INPUT across 3+ speech models (Sahara + 2 others). This script is
what's missing — run_asr_benchmark.py only tests the downstream risk
scorer on hand-written text, it never runs any ASR model on real audio.

This script:
    1. Loads real code-switched audio + ground-truth transcript pairs
       (from ml/data/synthetic/load_afriswitch.py output)
    2. Runs each audio clip through Sahara, Whisper, and MMS
    3. Computes WER for each model against ground truth
    4. Reports per-model WER (overall + numeric-figure-specific)
"""
import json
import re
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def word_error_rate(reference: str, hypothesis: str) -> float:
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


def numeric_word_error_rate(reference: str, hypothesis: str) -> float:
    """WER computed only on number-containing tokens — the metric that
    matters most for our fintech use case (misheard amounts)."""
    num_pattern = re.compile(r"\d+")
    ref_nums = [w for w in reference.split() if num_pattern.search(w)]
    hyp_nums = [w for w in hypothesis.split() if num_pattern.search(w)]
    if not ref_nums:
        return 0.0
    ref_str, hyp_str = " ".join(ref_nums), " ".join(hyp_nums)
    return word_error_rate(ref_str, hyp_str)


# ---- Model transcription wrappers ----
# Each of these takes a path/bytes to one audio clip and returns transcript text.
# Fill in the actual client calls once each is confirmed working individually.

def transcribe_sahara(audio_path: str) -> str:
    """
    TODO: call ml/../backend/app/services/sahara_asr.py's transcribe()
    on this audio file. Requires SAHARA_API_KEY + Integrator access.
    """
    raise NotImplementedError("Wire up Sahara STT call here")


def transcribe_whisper(audio_path: str) -> str:
    """
    Uses OpenAI's hosted Whisper API — no local GPU needed.
    Requires OPENAI_API_KEY environment variable set.
    """
    import os
    # OPENAI_API_KEY is separate from SAHARA_API_KEY; get it from platform.openai.com (requires billing enabled, ~$0.006/min of audio).
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set. Get it from platform.openai.com and set it before running Whisper benchmarks."
        )

    from openai import OpenAI
    client = OpenAI()  # reads OPENAI_API_KEY from environment automatically

    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text


def transcribe_mms(audio_path: str) -> str:
    """
    TODO: e.g. using HuggingFace transformers:
        from transformers import Wav2Vec2ForCTC, AutoProcessor
        processor = AutoProcessor.from_pretrained("facebook/mms-1b-all")
        model = Wav2Vec2ForCTC.from_pretrained("facebook/mms-1b-all")
        # set processor.tokenizer.set_target_lang("eng") or relevant language
        ... run inference, decode ...
    """
    raise NotImplementedError("Wire up MMS call here")


MODELS = {
    "sahara_v2": transcribe_sahara,
    "whisper_large_v3": transcribe_whisper,
    "meta_mms": transcribe_mms,
}


def run_comparison(test_set: list[dict]) -> dict:
    """
    test_set: [{"audio_path": str, "ground_truth": str, "is_code_switched": bool}, ...]
    Returns per-model WER, numeric WER, and latency, plus per-clip detail.
    """
    per_model_results = {name: {"wer": [], "numeric_wer": [], "latency": [], "errors": 0} for name in MODELS}
    per_clip_detail = []

    for clip in test_set:
        clip_result = {"audio_path": clip["audio_path"], "ground_truth": clip["ground_truth"], "transcripts": {}}

        for model_name, transcribe_fn in MODELS.items():
            start = time.time()
            try:
                hypothesis = transcribe_fn(clip["audio_path"])
                elapsed = time.time() - start
                wer = word_error_rate(clip["ground_truth"], hypothesis)
                num_wer = numeric_word_error_rate(clip["ground_truth"], hypothesis)

                per_model_results[model_name]["wer"].append(wer)
                per_model_results[model_name]["numeric_wer"].append(num_wer)
                per_model_results[model_name]["latency"].append(elapsed)
                clip_result["transcripts"][model_name] = {"text": hypothesis, "wer": wer, "numeric_wer": num_wer, "latency": elapsed}
            except NotImplementedError as e:
                per_model_results[model_name]["errors"] += 1
                clip_result["transcripts"][model_name] = {"error": str(e)}

        per_clip_detail.append(clip_result)

    summary = {}
    for model_name, stats in per_model_results.items():
        n = len(stats["wer"])
        summary[model_name] = {
            "avg_wer": round(sum(stats["wer"]) / n, 4) if n else None,
            "avg_numeric_wer": round(sum(stats["numeric_wer"]) / n, 4) if n else None,
            "avg_latency_sec": round(sum(stats["latency"]) / n, 3) if n else None,
            "clips_processed": n,
            "errors": stats["errors"],
        }

    return {"summary": summary, "per_clip_detail": per_clip_detail}


if __name__ == "__main__":
    test_set_path = ROOT_DIR / "ml" / "data" / "synthetic" / "asr_test_set.json"
    if not test_set_path.exists():
        print(
            f"No ASR test set found at {test_set_path}.\n"
            "This needs: [{'audio_path': ..., 'ground_truth': ..., 'is_code_switched': bool}, ...]\n"
            "Build this from ml/data/synthetic/load_afriswitch.py output — save a sample of "
            "real audio clips + their ground-truth transcripts to disk in this format."
        )
        sys.exit(1)

    test_set = json.loads(test_set_path.read_text())
    result = run_comparison(test_set)
    print(json.dumps(result["summary"], indent=2))

    out_path = ROOT_DIR / "ml" / "benchmarks" / "asr_comparison_results.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"\nFull results written to {out_path}")
