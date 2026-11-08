#!/usr/bin/env python3
"""facts/*.yaml を検査する: 必須欄、要点数、kind の語彙、thesis の有無、原文への漏洩。
usage: check_facts.py [facts_dir] [texts_dir]"""
import glob, os, re, sys
import yaml

# phase-1/check_leakage.py と同じ正規化・n-gram(import すると引数処理が走るので写す)
def norm(t):
    t = re.sub(r"```.*?```", "", t, flags=re.S); t = re.sub(r"\[コード\]", "", t)
    t = re.sub(r"https?://\S+", "", t); t = re.sub(r"^#+ .*$", "", t, flags=re.M)
    t = re.sub(r"^\s*(id|kind|scope|source|title|reader|points|facts|thesis):.*$", "", t, flags=re.M)
    return re.sub(r"\s", "", t)
def ng(t, n): return {t[i:i + n] for i in range(len(t) - n + 1)}
N = 10
# 言い回しの漏洩だけを見る版: ASCII の並び(識別子・コマンド・URL・数値)を落とす。
# 固有名は原文のまま書く規則なので、そこでの一致は言い回しの写しではない。
def ja(t): return re.sub(r"[\x21-\x7e]+", "", t)

facts_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "facts")
texts_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "texts/train")
KINDS = {"fact", "opinion", "example", "code"}
bad = 0
print(f"{'no':>2} {'pts':>3} {'op':>2} {'leak':>5} {'ja':>5} {'th_ja':>5} thesis   (leak=生, ja=ASCII除去後の言い回しのみ, th_ja=thesis の言い回し)")
for f in sorted(glob.glob(os.path.join(facts_dir, "*.yaml"))):
    no = os.path.basename(f)[:2]
    problems = []; notes = []
    try:
        d = yaml.safe_load(open(f, encoding="utf-8"))
    except Exception as e:
        print(f"{no} YAML が読めない: {e}"); bad += 1; continue
    for k in ("source", "title", "reader", "thesis", "points"):
        if not d.get(k): problems.append(f"{k} が無い")
    pts = d.get("points") or []
    if not 8 <= len(pts) <= 18: problems.append(f"要点 {len(pts)} 件")
    for p in pts:
        if p.get("kind") not in KINDS: problems.append(f"{p.get('id')}: kind={p.get('kind')}")
        if not p.get("claim"): problems.append(f"{p.get('id')}: claim が無い")
    srcs = glob.glob(os.path.join(texts_dir, f"{no}-*.md"))
    leak = tleak = jleak = float("nan")
    if srcs:
        o = ng(norm(open(srcs[0], encoding="utf-8").read()), N)
        c = ng(norm(open(f, encoding="utf-8").read()), N)
        leak = len(c & o) / max(len(c), 1) * 100
        src = open(srcs[0], encoding="utf-8").read()
        oj = ng(ja(norm(src)), N); cj = ng(ja(norm(open(f, encoding="utf-8").read())), N)
        jleak = len(cj & oj) / max(len(cj), 1) * 100
        t = ng(ja(re.sub(r"\s", "", str(d.get("thesis", "")))), N)
        hits = t & oj
        tleak = len(hits) / max(len(t), 1) * 100
        if jleak >= 5: problems.append(f"言い回しの漏洩 {jleak:.1f}%(生 {leak:.1f}%)")
        # thesis の一致は用語(「開発抽象化レイヤー」等)がほとんどなので、表示だけで不合格にはしない
        if hits: notes.append("thesis の一致: " + " / ".join(sorted(hits)[:4]))
    else:
        problems.append("原文が見つからない")
    ops = sum(1 for p in pts if p.get("kind") == "opinion")
    thesis = str(d.get("thesis", "")).replace("\n", " ")
    print(f"{no} {len(pts):3d} {ops:2d} {leak:5.1f} {jleak:5.1f} {tleak:5.0f} {thesis[:56]}")
    for n_ in notes: print(f"     - {n_}")
    if problems:
        bad += 1
        for p in problems: print(f"     ! {p}")
print(f"\n問題あり: {bad} 本")
sys.exit(1 if bad else 0)
