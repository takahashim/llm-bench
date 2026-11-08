#!/bin/bash
# v2: 反復抑止(DRY 0.8, repeat_penalty 1.1)で両条件を生成し直す。他は v1 と同じ
cd "$(dirname "$0")/.." || exit 1
exec >> phase-0/out/regen.log 2>&1
echo "== $(date '+%F %T') v2 生成開始"
python3 phase-0/generate_local.py --gguf phase-0/out/swallow-lora.Q8_0.gguf --out phase-0/candidates/lora --dry_multiplier 0.8 --repeat_penalty 1.1 || { echo "!! lora 失敗"; exit 1; }
python3 phase-0/generate_local.py --gguf phase-0/out/swallow-base.Q8_0.gguf --fewshot --out phase-0/candidates/fewshot --dry_multiplier 0.8 --repeat_penalty 1.1 || { echo "!! fewshot 失敗"; exit 1; }
python3 phase-0/make_rate_form.py || { echo "!! フォーム失敗"; exit 1; }
echo "== $(date '+%F %T') v2 全部終わった"
