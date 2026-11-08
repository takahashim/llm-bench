#!/bin/bash
# llm-jp を公式 llama.cpp の Vulkan ビルドで起動する。
# ollama の harmony パーサは SentencePiece の空白前置を解釈できないため、
# このモデルは ollama ではなく llama-server --jinja で動かす。
LC=${LC:-$HOME/bin/llama.cpp}
MODEL=${MODEL:-$HOME/models/llm-jp-4.1-32b-a3b-thinking-Q4_K_M.gguf}
PORT=${PORT:-8099}
# takahashim は render グループ非所属（ACL は物理シートに付与）なので sg で獲得する
exec sg render -c "LD_LIBRARY_PATH=$LC $LC/llama-server \
  -m $MODEL -ngl 99 -c 16384 --jinja --flash-attn on \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --host 127.0.0.1 --port $PORT"
