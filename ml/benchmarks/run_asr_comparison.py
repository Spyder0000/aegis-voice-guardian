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


def _normalize_text(text: str) -> str:
    # Lowercase and remove punctuation except spaces and digits
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return " ".join(text.split())


def _levenshtein_distance(ref_words: list[str], hyp_words: list[str]) -> int:
    m, n = len(ref_words), len(hyp_words)
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
    return dp[m][n]


def _extract_numeric_tokens(text: str) -> list[str]:
    num_pattern = re.compile(r"\d+")
    return [w for w in text.split() if num_pattern.search(w)]


def clean_ground_truth(text: str) -> str:
    """
    Strips timestamp patterns (e.g. 00:02:00, 00:05:98, 03:22:100) and speaker labels 
    (e.g. [Speaker 1]: or Speaker 1:) from ground-truth transcripts.
    """
    # Remove timestamps like 00:00:00 or 00:05:98 or 03:22:100
    cleaned = re.sub(r"\b\d{2}:\d{2}(?::\d{1,3})?\b", " ", text)
    # Remove speaker markers like [Speaker 1]: or Speaker 1:
    cleaned = re.sub(r"\[?Speaker\s*\d+\]?:?", " ", cleaned, flags=re.IGNORECASE)
    # Normalize whitespace
    return " ".join(cleaned.split())


def word_error_rate(reference: str, hypothesis: str) -> float:
    ref_clean = clean_ground_truth(reference)
    ref_words = _normalize_text(ref_clean).split()
    hyp_words = _normalize_text(hypothesis).split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0
    return _levenshtein_distance(ref_words, hyp_words) / len(ref_words)


from word2number import w2n

NUMBER_WORDS = {
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen",
    "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
    "hundred", "thousand", "million", "billion", "and", "a"
}


def is_number_word(word: str) -> bool:
    clean = re.sub(r"[^\w]", "", word).lower()
    return clean in NUMBER_WORDS or clean.isdigit()


def normalize_numbers(text: str) -> str:
    """Converts spelled-out number words to digits wherever possible."""
    words = text.split()
    normalized = []
    i = 0
    while i < len(words):
        matched = False
        for span in (4, 3, 2, 1):
            if i + span <= len(words):
                span_words = words[i : i + span]
                if all(is_number_word(w) for w in span_words):
                    candidate = " ".join(span_words)
                    cand_clean = re.sub(r"[^\w\s]", "", candidate)
                    try:
                        num = w2n.word_to_num(cand_clean)
                        normalized.append(str(num))
                        i += span
                        matched = True
                        break
                    except ValueError:
                        continue
        if not matched:
            normalized.append(words[i])
            i += 1
    return " ".join(normalized)



def numeric_word_error_rate(reference: str, hypothesis: str) -> float:
    ref_clean = clean_ground_truth(reference)
    ref_norm = normalize_numbers(ref_clean)
    hyp_norm = normalize_numbers(hypothesis)
    ref_nums = _extract_numeric_tokens(ref_norm)
    hyp_nums = _extract_numeric_tokens(hyp_norm)
    if not ref_nums:
        return 0.0 if not hyp_nums else 1.0
    ref_str = " ".join(ref_nums)
    hyp_str = " ".join(hyp_nums)
    return word_error_rate(ref_str, hyp_str)




# ---- Model transcription wrappers ----
# Each of these takes a path/bytes to one audio clip and returns transcript text.
# Fill in the actual client calls once each is confirmed working individually.

def transcribe_sahara(audio_path: str) -> str:
    """
    Calls Intron Sahara STT v2 WebSocket API on the audio file using SAHARA_API_KEY.
    Reads wave audio file frames, resamples to 16kHz if needed, and streams to WebSocket.
    """
    import asyncio
    import base64
    import json
    import os
    import wave
    import array
    from pathlib import Path
    import websockets

    # Load SAHARA_API_KEY from environment or .env file if available
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

    key = os.getenv("SAHARA_API_KEY", "")
    if not key:
        raise ValueError("SAHARA_API_KEY environment variable is not set.")

    def resample_to_16k(pcm_bytes: bytes, orig_sr: int) -> bytes:
        if orig_sr == 16000:
            return pcm_bytes
        samples = array.array("h", pcm_bytes)
        step = orig_sr / 16000.0
        resampled = array.array("h")
        idx = 0.0
        while int(idx) < len(samples):
            resampled.append(samples[int(idx)])
            idx += step
        return resampled.tobytes()

    async def wave_file_generator(path: str, chunk_bytes: int = 16000, max_sec: float = 240.0):
        with wave.open(path, "rb") as wf:
            orig_sr = wf.getframerate()
            nframes = wf.getnframes()
            max_frames = int(max_sec * orig_sr)
            read_len = min(nframes, max_frames)
            frames = wf.readframes(read_len)
            pcm_16k = resample_to_16k(frames, orig_sr)
            for i in range(0, len(pcm_16k), chunk_bytes):
                yield pcm_16k[i : i + chunk_bytes]
                await asyncio.sleep(0.001)



    async def _send_chunks(ws, chunks):
        ack_id = 0
        async for chunk in chunks:
            ack_id += 1
            await ws.send(json.dumps({
                "message_type": "INPUT_AUDIO_CHUNK",
                "audio_base_64": base64.b64encode(chunk).decode("utf-8"),
                "ack_id": ack_id
            }))
        await ws.send(json.dumps({"message_type": "COMMIT"}))

    async def _run():
        url = "wss://infer.voice.intron.io/stt/v1/stream?sample_rate=16000&bit_rate=16&num_channels=1&use_language_asr_input=en"
        headers = {"Authorization": f"Bearer {key}"}

        last_transcript = ""
        async with websockets.connect(url, additional_headers=headers, compression=None) as ws:
            first_raw = await ws.recv()
            first = json.loads(first_raw)
            if first.get("message_type") != "SESSION_CREATED":
                raise RuntimeError(f"Sahara ASR error: {first}")

            send_task = asyncio.create_task(_send_chunks(ws, wave_file_generator(audio_path)))

            async for raw in ws:
                event = json.loads(raw)
                msg_type = event.get("message_type")
                if event.get("transcript"):
                    last_transcript = event["transcript"]
                if msg_type in ("COMMITTED_TRANSCRIPT", "INSUFFICIENT_AUDIO_ACTIVITY"):
                    break
            send_task.cancel()

        return last_transcript

    return asyncio.run(_run())




def transcribe_whisper(audio_path: str) -> str:
    """
    Reads pre-computed Whisper transcripts generated via Google Colab.
    """
    lookup_path = ROOT_DIR / "ml" / "data" / "synthetic" / "whisper_transcripts.json"
    if not lookup_path.exists():
        raise FileNotFoundError(f"Missing pre-computed whisper transcripts at {lookup_path}")

    data = json.loads(lookup_path.read_text(encoding="utf-8"))
    filename = Path(audio_path).name

    if isinstance(data, list):
        for item in data:
            if item.get("audio_path") == filename or item.get("audio_path") == audio_path or item.get("id") == filename.replace(".wav", ""):
                return item.get("whisper_transcript", item.get("transcript", ""))
    elif isinstance(data, dict):
        if filename in data:
            return data[filename]
        if audio_path in data:
            return data[audio_path]

    raise ValueError(f"No whisper transcript found for {audio_path} in {lookup_path}")



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
            except (NotImplementedError, RuntimeError, ValueError) as e:
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
