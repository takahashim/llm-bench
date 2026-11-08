#!/usr/bin/env python3
"""著者が thesis を検証するためのフォームを作る。
各記事の title と thesis を並べ、「はい／いいえ／直す」を記入してもらう。"""
import glob, os, yaml
root = os.path.dirname(os.path.abspath(__file__))
rows = []
for f in sorted(glob.glob(os.path.join(root, "facts/*.yaml"))):
    d = yaml.safe_load(open(f, encoding="utf-8"))
    rows.append((os.path.basename(f)[:2], d.get("title", ""), str(d.get("thesis", "")).strip().replace("\n", " ")))
out = ["# thesis の検証(著者が記入)", "",
       "各記事について、thesis が「自分がこの記事で言いたかったこと」になっているかを見てください。",
       "原文は見なくて構いません(タイトルで思い出せる範囲で)。", "",
       "```", "○  そのとおり", "△  方向は合っているが、言いたいことの中心がずれている → 「直す」欄に一言",
       "×  そうではない → 「直す」欄に本当の主張を一文で", "```", "",
       "| No | 記事 | thesis(抽出) | ○△× | 直す |", "|---|---|---|---|---|"]
for no, title, thesis in rows:
    out.append(f"| {no} | {title} | {thesis} | | |")
out += ["", f"{len(rows)} 本。△× の thesis は `facts/NN.yaml` の `thesis:` を著者の文で置き換えて学習に使う。"]
open(os.path.join(root, "thesis_review.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print(f"thesis_review.md: {len(rows)} 本")
