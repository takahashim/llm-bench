#!/bin/bash
BENCH="$(cd "$(dirname "$0")/.." && pwd)"
cd "$(dirname "$0")/.."
source ../paths.sh
M="$1"; TYPE="$2"; NMAX="$3"; PROMPT="$4"
EXTRA=""
[ "$TYPE" != "${TYPE#draft}" ] && EXTRA="-md $D3"
OUT=$(./build/bin/llama-speculative-simple -m "$M" $EXTRA --spec-type "$TYPE" \
  -t 8 -td 8 -c 4096 --spec-draft-n-max "$NMAX" --spec-draft-n-min 0 \
  -n 160 --temp 0 -p "$PROMPT" 2>&1)
NP=$(echo "$OUT" | grep -oP 'n_predict = \K[0-9]+' | tail -1)
AC=$(echo "$OUT" | grep -oP 'accept    = \K[0-9.]+' | tail -1)
TT=$(echo "$OUT" | grep -oP 'total time =\s+\K[0-9.]+' | tail -1)
LT=$(echo "$OUT" | grep -oP 'load time =\s+\K[0-9.]+' | tail -1)
python3 -c "
np=${NP:-0}; tt=${TT:-0}; lt=${LT:-0}; ac='${AC:-n/a}'
gen=(tt-lt)/1000
print(f'{\"$TYPE\":<14} n_max={\"$NMAX\":<3} accept={ac:>7}%  {np:>4}tok / {gen:>6.1f}s = {np/gen if gen>0 else 0:>5.2f} tok/s')"
