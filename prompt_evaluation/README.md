# Prompt evaluation with DSPy and a local model

Measure a prompt instead of trusting it, then let an optimiser improve it. The example writes
AI governance exam questions (short answer and multiple choice) with Gemma 4 E2B, served on
your own machine by llama.cpp.

Companion page with setup, results and lessons: https://wmgmm.github.io/ai_governance/prompt_evaluation/

## The five steps

1. **Describe the task, not the prompt.** A DSPy signature names the inputs and outputs
   (`exam_qs.py`). DSPy writes the prompt, so an optimiser can change it.
2. **Collect examples, and keep some back.** 24 passages in `data/passages.jsonl`: 12 to
   train on, 12 held back. Every score comes from the held-back 12.
3. **Write down what "good" means.** The metric in `exam_qs.py` is a readable checklist
   (is it a question, does it stand alone, is the answer short and grounded, does the right
   option stand out by length). Test it on known-good answers before trusting it.
4. **Measure the starting point**, and measure the noise by running it again.
5. **Optimise, then measure again**: hand-written rules, BootstrapFewShot, MIPROv2, and
   MIPROv2 starting from the hand-written rules.

## Run it

```bash
./scripts/start_server.sh                  # terminal 1: llama-server on http://localhost:8090
uv sync                                    # terminal 2
uv run python run.py all                   # about 3 minutes on a desktop GPU
uv run python make_results_page.py         # rebuild the results on the companion page
```

The server script expects `gemma-4-E2B-it-Q8_0.gguf` in the Hugging Face cache
(`hf download ggml-org/gemma-4-E2B-it-GGUF gemma-4-E2B-it-Q8_0.gguf`), or set `MODEL=`.

## Files

| File | What it is |
|---|---|
| `exam_qs.py` | Signatures, data loading and the metric |
| `run.py` | One stage or all: `baseline`, `handwritten`, `bootstrap`, `mipro`, `combined`, `noise` |
| `make_results_page.py` | Writes `results/*.json` into `../site/prompt_evaluation/index.html` |
| `results/` | Scores, outputs, optimised programs and MIPROv2 logs from the last run |
| `data/passages.jsonl` | Passages with reference questions |

Tested with DSPy 3.4.0, llama.cpp 0.5.0 and Gemma 4 E2B Q8_0 (September 2026).
