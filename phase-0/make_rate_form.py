#!/usr/bin/env python3
"""LoRA 版と few-shot 版の候補をラベル無しで混ぜ、著者が評価するフォームを作る。

    python3 phase-0/make_rate_form.py            # candidates/{lora,fewshot} → rate/
    python3 phase-0/make_rate_form.py --score    # rate/form.md の記入を key で割って集計

どちらも著者の文章ではないので、ブラインドが成立する(SPEC 5 節)。
記事ごとに 2 本(a/b)を無作為に割り当て、対応は rate/key.json に書く。
**著者は key.json を開かない。** 集計は --score が行う。
"""
import argparse, glob, json, os, random, re
root = os.path.dirname(os.path.abspath(__file__))
p = argparse.ArgumentParser()
p.add_argument("--conds", nargs="+", default=["lora", "fewshot"])
p.add_argument("--score", action="store_true")
p.add_argument("--rate_dir", default="rate", help="フォームの置き場(0b は rate_0b)")
p.add_argument("--title", default="Phase 0a")
a = p.parse_args()
rate = os.path.join(root, a.rate_dir)

if not a.score:
    os.makedirs(rate, exist_ok=True)
    rng = random.Random(20261109)
    key, rows = {}, []
    ids = sorted(os.path.basename(f)[:2] for f in glob.glob(os.path.join(root, "candidates", a.conds[0], "*.md")))
    for no in ids:
        conds = a.conds[:]; rng.shuffle(conds)
        for letter, cond in zip("abcd", conds):
            src = os.path.join(root, "candidates", cond, f"{no}.md")
            text = open(src, encoding="utf-8").read()
            name = f"{no}{letter}"
            open(os.path.join(rate, f"{name}.md"), "w", encoding="utf-8").write(text)
            key[name] = cond
            rows.append(name)
    json.dump(key, open(os.path.join(rate, "key.json"), "w"), indent=1)
    lines = [f"# {a.title} 評価フォーム", "",
             f"`{a.rate_dir}/{rows[0]}.md` 〜 `{a.rate_dir}/{rows[-1]}.md` を読み、各候補を評価してください。",
             "同じ番号の a/b は同じ要点から別の方法で生成したものです。**原文は見ない。key.json は開かない。**", "",
             "```", "A  そのまま公開できる", "B  軽い手直しで公開できる", "C  大きく直す必要がある", "D  使えない", "",
             "主張: 強(著者が言いたいことを言っている) / 弱(要点を均等に並べているだけ)", "```", "",
             "C / D は問題の種類(構成 / 文体 / 内容 / その他)を一言で。", "",
             "| 候補 | 評価(A/B/C/D) | 主張(強/弱) | 問題の種類 | 一言 |", "|---|---|---|---|---|"]
    lines += [f"| {r} | | | | |" for r in rows]
    lines += ["", "合格ライン(SPEC 5 節): 各条件で A+B ≥ 7 かつ 主張「強」≥ 7。問いは LoRA が few-shot を上回るか。"]
    open(os.path.join(rate, "form.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"rate/form.md: {len(rows)} 本({len(ids)} 記事 × {len(a.conds)} 条件)")
else:
    key = json.load(open(os.path.join(rate, "key.json")))
    res = {c: {"grades": [], "strong": 0, "weak": 0, "problems": []} for c in a.conds}
    for line in open(os.path.join(rate, "form.md"), encoding="utf-8"):
        m = re.match(r"\|\s*(\d\d[a-d])\s*\|\s*([ABCD])\s*\|\s*([強弱]?)\s*\|\s*([^|]*)\|\s*([^|]*)\|", line)
        if not m: continue
        name, g, s, kind, note = m.groups(); c = key[name]
        res[c]["grades"].append(g)
        if s == "強": res[c]["strong"] += 1
        if s == "弱": res[c]["weak"] += 1
        if g in "CD": res[c]["problems"].append(f"{name}: {kind.strip()} {note.strip()}".strip())
    for c, r in res.items():
        g = r["grades"]; ab = sum(x in "AB" for x in g)
        print(f"{c:8s} n={len(g)}  A={g.count('A')} B={g.count('B')} C={g.count('C')} D={g.count('D')}  "
              f"A+B={ab}  主張 強={r['strong']} 弱={r['weak']}  "
              f"→ {'合格' if ab >= 7 and r['strong'] >= 7 else '不合格'}")
        for pr in r["problems"]: print("   ", pr)
