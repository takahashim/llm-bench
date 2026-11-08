#!/bin/bash
BENCH="$(cd "$(dirname "$0")/.." && pwd)"
# ロード時間を除去するため、n=160 と n=16 の実時間差で 144 token 分を測る
cd "$(dirname "$0")/.."
source ../paths.sh
M="$1"; TYPE="$2"; NMAX="$3"; PROMPT="$4"
EXTRA=""; [ "$TYPE" != "${TYPE#draft}" ] && EXTRA="-md $D3"
AC=""
run(){ local n=$1
  local t0=$(date +%s.%N)
  local out=$(./build/bin/llama-speculative-simple -m "$M" $EXTRA --spec-type "$TYPE" \
    -t 8 -td 8 -c 4096 --spec-draft-n-max "$NMAX" --spec-draft-n-min 0 \
    -n $n --temp 0 -p "$PROMPT" 2>&1)
  local t1=$(date +%s.%N)
  AC=$(echo "$out" | grep -oP 'accept    = \K[0-9.]+' | tail -1)
  echo "$t1 - $t0" | bc
}
T_LONG=$(run 160); T_SHORT=$(run 16)
python3 -c "
dt=${T_LONG}-${T_SHORT}
print(f'{\"$TYPE\":<14} n_max={\"$NMAX\":<3} accept={\"${AC:-n/a}\":>7}%  144tok / {dt:>5.1f}s = {144/dt if dt>0 else 0:>5.2f} tok/s')"
