#!/bin/bash
BENCH="$(cd "$(dirname "$0")/.." && pwd)"
cd $BENCH
source paths.sh
CORPUS="$1"; LABEL="$2"; CHUNKS="${3:-80}"
echo "########## perplexity: $LABEL (chunks=$CHUNKS, ctx=512) ##########"
for m in "$M30:Q4_K_M" "moe-q3km.gguf:Q3_K_M" "moe-iq3xxs.gguf:IQ3_XXS"; do
  path="${m%:*}"; name="${m##*:}"
  r=$(sg render -c "./llama.cpp/build/bin/llama-perplexity -m $path -f $CORPUS -c 512 --chunks $CHUNKS -ngl 99 2>&1" \
      | grep -oP 'Final estimate: PPL = \K[0-9.]+ \+/- [0-9.]+')
  echo "  $name  PPL = ${r:-FAILED}"
done
