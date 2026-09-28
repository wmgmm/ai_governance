#!/usr/bin/env bash
# Serve Gemma 4 E2B with llama.cpp on http://localhost:8090 (OpenAI-compatible at /v1).
# Override with: LLAMA_SERVER=/path/to/llama-server MODEL=/path/to/model.gguf PORT=8090
set -euo pipefail
LLAMA_SERVER="${LLAMA_SERVER:-$(command -v llama-server || echo "$HOME/src/llama.cpp/build/bin/llama-server")}"
MODEL="${MODEL:-$(ls "$HOME"/.cache/huggingface/hub/models--ggml-org--gemma-4-E2B-it-GGUF/snapshots/*/gemma-4-E2B-it-Q8_0.gguf 2>/dev/null | head -1)}"
PORT="${PORT:-8090}"
if [[ -z "$MODEL" ]]; then
  echo "Model not found. Download it with:" >&2
  echo "  hf download ggml-org/gemma-4-E2B-it-GGUF gemma-4-E2B-it-Q8_0.gguf" >&2
  exit 1
fi
# -ngl 99: put every layer on the GPU if there is one (ignored on CPU builds)
# --parallel 4: four request slots, so DSPy can evaluate four examples at once
# --reasoning off: Gemma 4 thinks by default; off is several times faster for short outputs
exec "$LLAMA_SERVER" -m "$MODEL" --alias gemma-4-e2b --port "$PORT" \
  -c 16384 --parallel 4 -ngl 99 --jinja --reasoning off
