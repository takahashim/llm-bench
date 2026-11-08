#!/bin/bash
# 学習の終了を待って、merge → GGUF → 生成(LoRA 版 / few-shot 版)→ 評価フォーム まで通す。
# Claude のセッションに依存させないための 1 本。setsid nohup で起動する。
set -u
cd "$(dirname "$0")/.." || exit 1
PY=phase-0/.venv/bin/python
MODEL=phase-0/models/swallow-8b-v0.5
exec >> phase-0/out/overnight.log 2>&1
step() { echo; echo "== $(date '+%F %T') $*"; }
fail() { echo "!! $(date '+%F %T') 失敗: $*"; exit 1; }

step "学習の終了を待つ"
until grep -qE "'event': 'done'|Traceback|Killed|MemoryError" phase-0/out/swallow-lora.log; do sleep 60; done
grep -qE "Traceback|Killed|MemoryError" phase-0/out/swallow-lora.log && fail "学習が落ちた(swallow-lora.log)"
grep -E "'event': 'val'" phase-0/out/swallow-lora.log

step "推論サーバ(llm-jp, :8099)を止める。GTT 30GiB に 21GB 居座っていて 8B Q8 が入らない"
pkill -f '[l]lama-server.*8099' && sleep 5 || echo "(動いていなかった)"

step "merge + GGUF(LoRA 版)"
$PY phase-0/merge_gguf.py --model $MODEL --adapter phase-0/out/swallow-lora --out phase-0/out/swallow-lora.Q8_0.gguf || fail "LoRA 版の変換"

step "GGUF(base 版、few-shot 対照用)"
if [ -s phase-0/out/swallow-base.Q8_0.gguf ]; then echo "(既にある)"; else
  $PY phase-0/merge_gguf.py --model $MODEL --out phase-0/out/swallow-base.Q8_0.gguf || fail "base 版の変換"; fi

step "生成: LoRA 版"
python3 phase-0/generate_local.py --gguf phase-0/out/swallow-lora.Q8_0.gguf --out phase-0/candidates/lora || fail "LoRA 版の生成"
step "生成: few-shot 版"
python3 phase-0/generate_local.py --gguf phase-0/out/swallow-base.Q8_0.gguf --fewshot --out phase-0/candidates/fewshot || fail "few-shot 版の生成"

step "評価フォーム"
python3 phase-0/make_rate_form.py || fail "フォーム"
step "全部終わった"
