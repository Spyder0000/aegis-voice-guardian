# AEGIS Voice Guardian — Benchmark Report
**Requirement:** compare performance across 3+ speech models, including Sahara, plus 2+ others.

## Models Compared
| Model | Type | Why chosen |
|---|---|---|
| Intron Sahara v2 | Commercial API | Our core ASR — purpose-built for African accents/code-switching/numeric precision |
| OpenAI Whisper (large-v3) | Open-source, global | Widely-used baseline; shows what a global model misses on African speech |
| [FILL IN: e.g. Meta MMS, or a fine-tuned wav2vec2 African model] | Open-source, local/regional | Shows performance of a non-Sahara model built with African languages in mind |

**[TODO: confirm your third model choice now — pick whichever you can get running fastest given time left. MMS (`facebook/mms-1b-all`) or a Common Voice-finetuned Wav2Vec2 model are reasonable if you need something quick via HuggingFace.]**

## Test Data
- **Source:** [Intron's open code-switching benchmark collection](https://huggingface.co/collections/intronhealth/code-switching) — specifically the **Intron Afriswitch** dataset (natural code-switching across 12+ languages), sampled for English/Pidgin and English/Yoruba examples relevant to our Nigerian fintech use case.
- **Supplemented with:** our own scripted scam vs. genuine transfer-call audio (see `ml/data/synthetic/`), generated to test the specific phrases and numeric patterns our Trust Score depends on (currency figures, urgency language, authority-impersonation phrases).
- **Sample size:** [FILL IN — how many audio clips you actually ran through all 3 models]

## Metrics

### 1. Word Error Rate (WER)
Standard ASR accuracy metric — lower is better. Reported separately for:
- Overall transcript
- **Numeric figures specifically** (Naira amounts) — this is the metric that matters most for our use case, since a misheard amount is the core risk AEGIS is designed to prevent
- Code-switched segments specifically (English/Pidgin, English/Yoruba)

| Model | Overall WER | Numeric WER | Code-switch WER |
|---|---|---|---|
| Sahara v2 | [FILL IN] | [FILL IN] | [FILL IN] |
| Whisper large-v3 | [FILL IN] | [FILL IN] | [FILL IN] |
| [Third model] | [FILL IN] | [FILL IN] | [FILL IN] |

### 2. Entity Extraction Accuracy
Given the transcript, how accurately can amount/recipient/urgency-phrase entities be pulled out? (Run the same extraction logic against each model's transcript output.)

| Model | Amount extraction accuracy | Recipient extraction accuracy | Urgency-phrase detection recall |
|---|---|---|---|
| Sahara v2 | [FILL IN] | [FILL IN] | [FILL IN] |
| Whisper large-v3 | [FILL IN] | [FILL IN] | [FILL IN] |
| [Third model] | [FILL IN] | [FILL IN] | [FILL IN] |

### 3. Downstream Intervention Accuracy (AEGIS-specific, our own contribution)
This is the metric that ties ASR quality directly to real-world impact — how often does a transcription error from each model change what AEGIS actually *does* (i.e., release money it should have held, or hold money it shouldn't have)?

| Model | False positive rate (genuine flagged as risky) | False negative rate (scam missed) |
|---|---|---|
| Sahara v2 | [FILL IN — from Toluwalase's benchmark harness] | [FILL IN] |
| Whisper large-v3 | [FILL IN] | [FILL IN] |
| [Third model] | [FILL IN] | [FILL IN] |

### 4. Latency
| Model | Avg time (audio-in → transcript-out) |
|---|---|
| Sahara v2 | [FILL IN] |
| Whisper large-v3 | [FILL IN] |
| [Third model] | [FILL IN] |

## Pros and Cons

**Intron Sahara v2**
- Pros: [FILL IN based on actual results — likely: strongest on Nigerian-accented numeric figures and code-switching, purpose-built for this exact use case]
- Cons: [FILL IN — e.g., WebSocket session cap at 300s requires reconnect handling; TTS reply capped at 100 characters]

**Whisper large-v3**
- Pros: free, open-source, no session limits, widely documented
- Cons: [FILL IN based on actual results — likely: weaker on code-switched segments and African-accented numeric figures, which is exactly the gap Sahara is built to close]

**[Third model]**
- Pros: [FILL IN]
- Cons: [FILL IN]

## Conclusion
[FILL IN once results are in — 2-3 sentences on which model best supports the actual product decision (holding/releasing real money) and why raw WER alone isn't the whole story — the downstream intervention accuracy is what actually matters for this use case.]

---
**How to run this:**
1. `ml/benchmarks/run_asr_benchmark.py` (Toluwalase) already computes WER and the intervention FP/FN rate — point it at outputs from all 3 models once you have transcripts from each
2. Feed the same audio clips through Sahara, Whisper, and the third model — save each model's raw transcript output
3. Fill in every `[FILL IN]` above with the real numbers
