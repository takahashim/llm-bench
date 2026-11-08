# llm-bench

bear1（Ryzen 7 8745H / Radeon 780M / 64GB DDR5-5600）でのローカルLLM測定一式。
測定日 2026-11-04 〜 11-08。詳細なスペックシートは別途 Claude Docs にある。

## 要点

このマシンの性能は2つの式で決まる。

```
① decode tok/s ≈ 到達帯域 ÷ 1トークンあたり読むバイト数   ← ハードの法則
② 実時間       = 答えまでのトークン数 ÷ decode tok/s      ← モデル選択が支配
```

到達帯域は **iGPU 約80 GB/s / CPU 約57 GB/s**（DRAM理論は89.6）。
CPU側の57はコア側の制約で、iGPUはこれを迂回する。

①は設定とモデルクラスの選択で 3.07倍 改善した（11.78 → 36.12 tok/s）。
②はモデルを変えるだけで 4.75倍 動いた。②はハードを買い替えても改善しない。

## 効いたもの / 効かなかったもの

| 手 | 結果 |
|---|---|
| `OLLAMA_IGPU_ENABLE=1` | **1.45倍**。無いと100% CPUで動く |
| MoE（qwen3:30b-a3b） | **2.3倍**。dense 8Bに対して |
| `OLLAMA_FLASH_ATTENTION=1` | **16K文脈で2.91倍**。ollamaのデフォルトは無効 |
| 公式ビルド済みバイナリ | prefill **+8.3%**（`int dot: 1`）。decodeは不変 |
| 低ビット量子化（Q3/IQ3） | 速度+13%、PPL+16〜28%。**割に合わない** |
| 投機デコード | dense 1.13〜1.37倍、**MoEでは逆効果**（0.70倍） |
| ngram系 | **効果ゼロ** |
| バッチ | denseは3.4倍、**MoEは1.5倍で飽和**（B=8で両者約53 tok/s） |

## ディレクトリ

```
scripts/   測定スクリプト
  bw.c rd.c        メモリ帯域（CPU、AVX2ストリーミング）
  spec*.sh         投機デコード（CPU版 / GPU版 / 校正済み）
  ppl.sh           perplexity（llama-perplexity）
  p1.py p3.py      モデル比較（軽い4問）
  heavy.py cmp.py  モデル比較（重い3問）
results/   測定結果 JSON（回答本文・トークン数・実時間つき）
data/      日本語コーパス（ja-wiki.txt / src_text.txt）
run-server.sh      llm-jp を llama-server で起動
```

## 注意

- GPU を使うには `sg render -c '<cmd>'` が要る（このユーザーは render グループ非所属）
- `llm-jp-4.1-32b-a3b-thinking` は **ollama では動かない**。ollamaのharmonyパーサが
  SentencePieceの空白前置（`<|channel|> analysis`）を解釈できないため。
  公式llama.cppの `llama-server --jinja` を使う（`run-server.sh`）
- results/ の品質評価は n=7・各1サンプルの読み比べにすぎない。**精度は測っていない**。
  比べるなら llm-jp-eval や JMMLU などの標準ベンチを使うこと

## データの出典

`data/ja-wiki.txt` と `data/src_text.txt` は **日本語版ウィキペディア**から取得した
テキストである。

- 取得日: 2026-11-04
- 取得方法: MediaWiki API (`action=query&prop=extracts&generator=random`) で
  ランダムに記事本文を取得し連結。`src_text.txt` はその先頭2,400字
- 用途: perplexity測定（`scripts/ppl.sh`）と要約タスクの題材
- ライセンス: **CC BY-SA 4.0** — https://creativecommons.org/licenses/by-sa/4.0/
- 原典: https://ja.wikipedia.org/

このリポジトリを再配布する場合、これらのファイルは CC BY-SA 4.0 の条件下にある。
同一コーパスを保持しているのは、量子化ごとの perplexity 比較（Q4_K_M 6.418 /
Q3_K_M 7.277 / IQ3_XXS 7.428）を再現可能にするため。別のサンプルでは比較にならない。
