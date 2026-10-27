#!/usr/bin/env bash
# Round 3 (26 Oct 2026): serve ONE parser model with vLLM on 127.0.0.1:8001 for parser_eval.py.
#   bash round3_serve.sh <nemotronparse|paddleocrvl16|olmocr2>
# Started by tools/round3_driver.py as a child of a wsl.exe process, so stopping that process stops the server.
# Log: ~/round3_serve_<key>.log inside Ubuntu.
set -u
KEY="$1"
export CUDA_HOME=/usr/local/cuda-13.0
export PATH="$CUDA_HOME/bin:$PATH"
COMMON=(--host 127.0.0.1 --port 8001 --served-model-name "$KEY" --limit-mm-per-prompt '{"image":1}')
case "$KEY" in
  nemotronparse)
    source "$HOME/parse/bin/activate"
    cd "$HOME/nemotron-parse"
    ARGS=(. --dtype bfloat16 --distributed-executor-backend uni --tensor-parallel-size 1 --max-model-len 16384
          --max-num-seqs 64 --max-num-batched-tokens 16384 --no-enable-prefix-caching --trust-remote-code
          --chat-template chat_template.jinja --gpu-memory-utilization 0.60) ;;
  paddleocrvl16)
    source "$HOME/vllm/bin/activate"
    ARGS=(PaddlePaddle/PaddleOCR-VL-1.6 --trust-remote-code --max-model-len 16384 --max-num-batched-tokens 16384
          --no-enable-prefix-caching --mm-processor-cache-gb 0 --gpu-memory-utilization 0.60) ;;
  olmocr2)
    source "$HOME/vllm/bin/activate"
    ARGS=(allenai/olmOCR-2-7B-1025-FP8 --max-model-len 16384 --gpu-memory-utilization 0.85) ;;
  *) echo "unknown model key: $KEY"; exit 2 ;;
esac
echo "=== start $(date -Is) $KEY" >> "$HOME/round3_serve_$KEY.log"
exec vllm serve "${ARGS[@]}" "${COMMON[@]}" >> "$HOME/round3_serve_$KEY.log" 2>&1
