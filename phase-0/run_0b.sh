#!/bin/bash
# Phase 0b: llm-jp-4.1-8b-thinking。学習の終了を待って merge → GGUF → 生成 → フォーム。
# 条件: llmjp-lora(LoRA、思考なしで直接)、llmjp-fewshot(base、思考あり、著者記事 3 本を手本)。
# 問い: LoRA 後に、思考なしで同等品質を直接生成のコストで出せるか。トークン数と時間も記録する。
set -u
cd "$(dirname "$0")/.." || exit 1
PY=phase-0/.venv/bin/python
MODEL=phase-0/models/llmjp-8b-thinking
exec >> phase-0/out/run_0b.log 2>&1
step() { echo; echo "== $(date '+%F %T') $*"; }
fail() { echo "!! $(date '+%F %T') 失敗: $*"; exit 1; }

step "学習の終了を待つ"
until grep -qE "'event': 'done'|Traceback|Killed|MemoryError" phase-0/out/llmjp-lora.log; do sleep 60; done
grep -qE "Traceback|Killed|MemoryError" phase-0/out/llmjp-lora.log && fail "学習が落ちた(llmjp-lora.log)"
grep -E "'event': 'val'" phase-0/out/llmjp-lora.log

step "GGUF(base 版)"
if [ -s phase-0/out/llmjp-base.Q8_0.gguf ]; then echo "(既にある)"; else
  $PY phase-0/merge_gguf.py --model $MODEL --out phase-0/out/llmjp-base.Q8_0.gguf || fail "base 版の変換"; fi
step "merge + GGUF(LoRA 版)"
$PY phase-0/merge_gguf.py --model $MODEL --adapter phase-0/out/llmjp-lora --out phase-0/out/llmjp-lora.Q8_0.gguf || fail "LoRA 版の変換"

pgrep -f '[l]lama-server -m' >/dev/null && { echo "他の llama-server が動いている。止める"; pkill -f '[l]lama-server -m'; sleep 5; }
step "生成: LoRA 版(思考なしを期待。出たら reasoning として記録される)"
python3 phase-0/generate_local.py --gguf phase-0/out/llmjp-lora.Q8_0.gguf --out phase-0/candidates/llmjp-lora --dry_multiplier 0.8 --repeat_penalty 1.1 --max_tokens 12000 || fail "LoRA 版の生成"
step "生成: few-shot 版(base、思考あり)"
python3 phase-0/generate_local.py --gguf phase-0/out/llmjp-base.Q8_0.gguf --fewshot --out phase-0/candidates/llmjp-fewshot --dry_multiplier 0.8 --repeat_penalty 1.1 --max_tokens 12000 || fail "few-shot 版の生成"

step "評価フォーム"
python3 phase-0/make_rate_form.py --conds llmjp-lora llmjp-fewshot --rate_dir rate_0b --title "Phase 0b" || fail "フォーム"
step "全部終わった"
