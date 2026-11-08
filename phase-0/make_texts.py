#!/usr/bin/env python3
"""pool.json から学習用の本文を書き出す。

評価用10本（phase-1/selection.json の eval）は学習に使わない。few-shot の5本は学習に回す。
SPEC 7節の除外（政府文書の転載、年表、参考情報のリンク集）はここで落とす。
本文は phase-1/texts と同じ形: コードブロックは [コード] に置換済み、タイトル行なし。
"""
import json, re, pathlib
root = pathlib.Path(__file__).resolve().parent
pool = json.load(open(root.parent / "phase-1/pool.json", encoding="utf-8"))
sel = json.load(open(root.parent / "phase-1/selection.json", encoding="utf-8"))
eval_ids = {e["id"] for e in sel["eval"]}

EXCLUDE = {
    "add456bf65ba51": "政府文書の転載",
    "5bed337cc35e85": "政府文書の転載",
    "077a1eeba805c7": "年表。説明文ではない",
    "7501bfa3974890": "参考情報のリンク集。説明文ではない",
}

out = root / "texts/train"
rows = []
n = 0
for a in pool:
    aid = a["id"][:14]
    if a["id"] in eval_ids or aid in eval_ids:
        continue
    if aid in EXCLUDE:
        rows.append({"id": aid, "title": a["title"], "excluded": EXCLUDE[aid]})
        continue
    n += 1
    text = re.sub(r"```.*?```", "[コード]", a["text"], flags=re.S).strip() + "\n"
    name = f"{n:02d}-{a['src']}-{aid}.md"
    (out / name).write_text(text, encoding="utf-8")
    rows.append({"n": n, "file": f"texts/train/{name}", "src": a["src"], "id": aid,
                 "date": a["date"], "title": a["title"], "prose": int(a["prose"]),
                 "code": int(a["code"]), "fewshot_in_phase_1": a["id"] in {e["id"] for e in sel["fewshot"]}})
json.dump({"train": [r for r in rows if "n" in r], "excluded": [r for r in rows if "excluded" in r]},
          open(root / "train_set.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"train {n} 本, excluded {len(EXCLUDE)} 本, eval (phase-1) {len(eval_ids)} 本")
