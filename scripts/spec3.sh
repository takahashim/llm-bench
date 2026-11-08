#!/bin/bash
BENCH="$(cd "$(dirname "$0")/.." && pwd)"
# GPU版: n=160 と n=16 の実時間差で 144 token を測る
cd "$(dirname "$0")/.."
source ../paths.sh
M="$1"; TYPE="$2"; NMAX="$3"; PROMPT="$4"
EXTRA=""; [ "$TYPE" != "${TYPE#draft}" ] && EXTRA="-md $D3 -ngld 99"
AC=""
run(){ local t0=$(date +%s.%N)
  local out=$(./build/bin/llama-speculative-simple -m "$M" $EXTRA --spec-type "$TYPE" \
    -ngl 99 -c 4096 --spec-draft-n-max "$NMAX" --spec-draft-n-min 0 \
    -n $1 --temp 0 -p "$PROMPT" 2>&1)
  local t1=$(date +%s.%N)
  AC=$(echo "$out" | grep -oP 'accept    = \K[0-9.]+' | tail -1)
  echo "$t1 - $t0" | bc
}
L=$(run 160); S=$(run 16)
python3 -c "
dt=${L}-${S}
print(f'{\"$TYPE\":<14} n_max={\"$NMAX\":<3} accept={\"${AC:-n/a}\":>7}%  144tok / {dt:>5.1f}s = {144/dt if dt>0 else 0:>5.2f} tok/s')"
