#!/usr/bin/env python3
"""facts/*.yaml と texts/train/*.md から学習用の (入力 → 本文) 対を作る。

入力は「題・読者・主張・要点(順序はファイルのまま = シャッフル済み)」を1つの指示文に
したもの。出力は著者の本文そのまま(コードブロックは [コード] のまま。生成側に
コードを書かせないため)。

形式は chat 1往復 (messages) の JSONL。unsloth / TRL の SFTTrainer がそのまま読む。
評価用の 10 本 (phase-1/facts_coarse) も同じ形で eval.jsonl に書く(本文は付けない)。
"""
import glob, json, os, random, yaml
root = os.path.dirname(os.path.abspath(__file__))

SYSTEM = ("あなたは日本語の技術記事を書く書き手です。与えられた主張と要点だけを使って、"
          "読者が理解しやすい解説文を書いてください。要点に無い情報(数値・URL・固有名)を"
          "足してはいけません。コードは [コード] と書くだけにしてください。")

def prompt(d):
    lines = [f"# 題\n{d['title']}", f"# 読者\n{d['reader']}", "# 要点"]
    if d.get("thesis"): lines.insert(2, f"# 主張\n{d['thesis'].strip()}")
    for p in d["points"]:
        s = f"- {p['claim'].strip()}"
        if p.get("scope"): s += f"(条件: {p['scope'].strip()})"
        if p.get("kind") == "code": s += "(コード)"
        lines.append(s)
    return "\n".join(lines)

def pairs(facts_dir, texts_dir, with_text=True):
    out = []
    for f in sorted(glob.glob(os.path.join(facts_dir, "*.yaml"))):
        d = yaml.safe_load(open(f, encoding="utf-8"))
        no = os.path.basename(f)[:2]
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt(d)}]
        if with_text:
            src = glob.glob(os.path.join(texts_dir, f"{no}*.md"))[0]
            msgs.append({"role": "assistant", "content": open(src, encoding="utf-8").read().strip()})
        out.append({"id": no, "title": d["title"], "messages": msgs})
    return out

train = pairs(os.path.join(root, "facts"), os.path.join(root, "texts/train"))
random.Random(42).shuffle(train)
# 3 本を loss の監視用に抜く。評価(著者の判定)は phase-1 の 10 本で行い、こちらは数値だけ
val, train = train[:3], train[3:]
ev = pairs(os.path.join(root, "../phase-1/facts_coarse"), None, with_text=False)
for name, rows in (("train", train), ("val", val), ("eval", ev)):
    with open(os.path.join(root, "data", f"{name}.jsonl"), "w", encoding="utf-8") as w:
        for r in rows: w.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{name}: {len(rows)} 本", "" if not rows else f"(例: {rows[0]['id']} {rows[0]['title'][:30]})")
n = sum(len(m["content"]) for r in train for m in r["messages"])
print(f"train の総文字数 {n:,}(prompt + 本文)")
