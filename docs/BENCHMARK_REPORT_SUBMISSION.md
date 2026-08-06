# AEGIS Voice Guardian — Code-Switching ASR Benchmark Report
**Deep Learning Indaba 2026 — "Whose Intelligence?" Hackathon Submission**

---

## 1. Models Compared

| Model | Type | Pros | Cons | Evaluation Status |
|---|---|---|---|---|
| **Intron Sahara v2** | Commercial API | High fluency on African accents & clinical terms; robust against non-linguistic hallucinations | Bounded by 300s per-session streaming limit; higher streaming latency (~52s/clip) | **Executed** (5 real clips) |
| **OpenAI Whisper (large-v3)** | Open-source, global | Unbounded audio processing length; near-instant local batch inference (~0.04s/clip) | Prone to non-linguistic hallucinations and text corruption on code-switched dialogue turns | **Executed** (5 real clips) |
| **Meta MMS (`facebook/mms-1b-all`)** | Open-source, regional | Purpose-built regional architecture covering 1,000+ African and global languages | High memory footprint; integration not completed within 72-hour build window | *Not Executed* (Future baseline) |

---

## 2. Data Description

- **Source:** [Intron Afriswitch Dataset (HuggingFace)](https://huggingface.co/collections/intronhealth/code-switching) — `intronhealth/afrispeech-dialog` collection featuring natural African code-switched dialogues.
- **Sample Size & Duration:** 5 real code-switched audio clips totaling **2,441.84 seconds (~40.70 minutes / 0.68 hours)** of continuous dialogue speech.
- **Clip-Level Language Metadata:**

| Clip ID | Language / Accent Tag | Country | Duration | Ground-Truth Dialogue Type |
|---|---|---|---|---|
| `clip_0` | English / Hausa code-switched | Nigeria (`NG`) | 2.47 min (148.5s) | Medical dialogue |
| `clip_1` | English / Isoko code-switched | Nigeria (`NG`) | 3.50 min (209.9s) | Medical dialogue |
| `clip_2` | English / Isoko code-switched | Nigeria (`NG`) | 14.91 min (894.4s) | Medical dialogue |
| `clip_3` | English / Hausa code-switched | Nigeria (`NG`) | 15.70 min (941.9s) | Medical dialogue |
| `clip_4` | English / Hausa code-switched | Nigeria (`NG`) | 4.12 min (247.1s) | Medical dialogue |

- **Preprocessing:** Ground-truth text was preprocessed by stripping non-spoken metadata headers (e.g. `00:02:00` timestamps and `[Speaker 1]:` markers) and applying bidirectional number normalization (`word2number`) to map spelled-out number words (e.g. "sixty five" $\rightarrow$ "65") into single digit tokens for fair evaluation.

---

## 3. Evaluation Metrics

- **Word Error Rate (WER):** Standard ASR accuracy metric measuring word insertions, deletions, and substitutions relative to ground truth (lower is better).
- **Numeric WER:** Evaluates error rates specifically on extracted numerical digit tokens to isolate performance on transaction-critical figures (e.g. transfer amounts and account numbers) for our fintech use case.

---

## 4. Quantitative Results PER LANGUAGE

| Language / Accent Group | Clips | Model | Corrected Avg WER | Final Avg Numeric WER | Avg Latency |
|---|---|---|---|---|---|
| **English / Hausa Code-Switched** | 3 clips (`clip_0`, `clip_3`, `clip_4`) | **Sahara v2** | **69.88%** | **92.02%** | ~209.0s/clip |
| | | **Whisper large-v3** | **57.34%** | **37.37%** | ~0.05s/clip |
| | | **Meta MMS-1B** | *Not Executed* | *Not Executed* | N/A |
| **English / Isoko Code-Switched** | 2 clips (`clip_1`, `clip_2`) | **Sahara v2** | **47.71%** | **32.14%** | ~304.6s/clip |
| | | **Whisper large-v3** | **41.55%** | **10.71%** | ~0.04s/clip |
| | | **Meta MMS-1B** | *Not Executed* | *Not Executed* | N/A |
| **Overall Benchmark Average** | 5 clips total (40.7 min) | **Sahara v2** | **61.01%** | **68.07%** | ~261.0s/clip |
| | | **Whisper large-v3** | **51.02%** | **26.71%** | ~0.04s/clip |
| | | **Meta MMS-1B** | *Not Executed* | *Not Executed* | N/A |

*Note on Sample Scope:* The evaluated sample consists of 5 code-switched dialogues across English/Hausa and English/Isoko accents from Nigeria; results are presented per language group above and averaged across the benchmark dataset.

![WER Comparison](charts/wer_comparison.png){width=80%}

---

## 5. Qualitative Findings PER MODEL PER LANGUAGE

- **Intron Sahara v2:** Across both Hausa and Isoko code-switched dialogue clips, Sahara demonstrated superior phonetic and vocabulary fidelity, producing grammatically coherent and accurately punctuated transcripts. However, on long clips (`clip_2` & `clip_3`), Sahara encountered Intron's documented 300-second per-session streaming limit (`SESSION_TIME_LIMIT_EXCEEDED` at 326.3s), truncating audio processing and inflating its aggregate WER on those long clips.
- **OpenAI Whisper (large-v3):** While Whisper scored lower overall WER due to handling unbounded audio length, it exhibited severe non-linguistic hallucination failures on code-switched dialogue turns. On `clip_0` (Hausa accent), Whisper outputted unreadable non-linguistic character strings (`\u0f71\u0f71\u0f61...`), and on `clip_1` (Isoko accent), it degenerated into repetitive string loops (`No. No. No. No...`), creating unacceptable operational risk for financial voice intake.
- **Meta MMS-1B:** Explicitly marked as *Not Executed* due to hackathon time constraints; retained in documentation as a baseline reference for future regional model evaluation.
