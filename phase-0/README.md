# Phase 0a: 著者の記事で Swallow-8B に LoRA を当てる

問い: LoRA は few-shot より著者の文章に近づくか(SPEC 6 節)。

## 流れ

```
make_texts.py      pool.json → texts/train/ (36 本)                 済
EXTRACT.md         工程A の規則。Opus のエージェントが facts/ を書く    済 (NOTES.md)
check_facts.py     欄・件数・漏洩の検査                              済、全件合格
make_review.py     thesis_review.md。著者が見る                       済 (「悪くはない」)
build_dataset.py   facts + texts → data/{train,val,eval}.jsonl       33 / 3 / 10 本
train.py           QLoRA (unsloth)。adapter を保存                   ← ここから GPU
generate.py        eval 10 本を LoRA 版と few-shot 版で生成
rate/              著者が 4 段階 + 主張の強弱で評価 (phase-1 と同じ形式)
```

## 学習を回す場所

bear1(Radeon iGPU、Vulkan)では学習できない。選択肢は 2 つ。

| | 手間 | 費用 | 備考 |
|---|---|---|---|
| **HF Jobs**(`hf jobs uv run`) | 最小。ログイン済み | L40S 48GB $1.80/h、A10G 24GB $1.50/h。1 回 20〜40 分で $1〜2 | private の dataset repo 1 つに data / lora / candidates を全部置く |
| RTX 3080 16GB のノート PC | Linux(or WSL2)+ CUDA + unsloth の導入 | 電気代 | 8B 4bit + 8k 系列は 16GB でぎりぎり。max_seq を 4096 に落とす必要があるかもしれない |

### HF Jobs の手順

置き場所は private の dataset repo **1 つ**: `takahashim/llm-bench-phase0`。
`data/`(学習データ)、`lora/`(adapter)、`candidates/`(生成物)を全部ここに置く。
Jobs はこの repo を `/mnt/d` にマウントするので、adapter もマウントしたパスから読む。
git(このリポジトリ)にはスクリプトと要点だけを置き、HF 側は成果物の置き場と割り切る。

```sh
REPO=takahashim/llm-bench-phase0
V="-v hf://datasets/$REPO:/mnt/d"

# 1. データを上げる(本文は著者の記事。public にしない)
hf upload $REPO phase-0/data data --type dataset --private

# 2. 学習。adapter は同じ repo の lora/ へ
hf jobs uv run phase-0/train.py --flavor l40sx1 --timeout 2h --secrets HF_TOKEN $V \
  -- --data /mnt/d/data --out /tmp/lora --push $REPO

# 3. 生成(LoRA 版と few-shot 版)。candidates/{lora,fewshot}/ に上がる
hf jobs uv run phase-0/generate.py --flavor l40sx1 --timeout 1h --secrets HF_TOKEN $V \
  -- --data /mnt/d/data --adapter /mnt/d/lora --out /tmp/lora --push_dataset $REPO
hf jobs uv run phase-0/generate.py --flavor l40sx1 --timeout 1h --secrets HF_TOKEN $V \
  -- --data /mnt/d/data --fewshot --out /tmp/fewshot --push_dataset $REPO

# 4. 回収
hf download $REPO --type dataset --include 'candidates/*' 'lora/*' --local-dir phase-0
```

マウントは Job 開始時点の内容なので、2 の push 後に 3 を起動すれば lora/ が見える。

`train.py` と `generate.py` は PEP 723 の依存宣言つきなので `uv run` がそのまま環境を作る。

## 学習の設定(train.py の既定)

| | |
|---|---|
| base | tokyotech-llm/Llama-3.1-Swallow-8B-Instruct-v0.5(非 thinking、gated なし) |
| 量子化 | 4bit(QLoRA) |
| LoRA | r=16、alpha=32、q/k/v/o/gate/up/down |
| 系列長 | 8192(23 の 16,500 字記事は切られる) |
| 学習 | 3 epoch、lr 2e-4 cosine、batch 1 × accum 8 → 約 12 step |
| loss | assistant(本文)のみ。prompt(要点)は学習しない |

33 本 × 3 epoch は少ない。過学習を疑うより先に「何も変わらない」を疑う量なので、
val loss の前後と、生成物の著者評価で判断する。

## 対照

1. **同じ base の few-shot**(`generate.py --fewshot`)。学習データ中の短い 3 本を手本に入れる。
   LoRA と同じ情報しか見ていないので、公平な対照
2. **Phase -1 の Opus few-shot**(`phase-1/candidates_coarse/`)。thesis 無しで生成したもの。
   天井の目安だが、thesis の有無が違うので直接比較はしない

## 評価

phase-1/rate/form.md と同じ: 原文は見ない、A/B/C/D、主張の強/弱。
LoRA 版と few-shot 版をラベル無しで混ぜる(どちらも著者の文章ではないのでブラインドが成立する)。
