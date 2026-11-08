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

facts_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "facts")
texts_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "texts/train")
KINDS = {"fact", "opinion", "example", "code"}
bad = 0
print(f"{'no':>2} {'pts':>3} {'op':>2} {'leak':>5} {'thesis_leak':>11} thesis")
for f in sorted(glob.glob(os.path.join(facts_dir, "*.yaml"))):
    no = os.path.basename(f)[:2]
    problems = []
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
    leak = tleak = float("nan")
    if srcs:
        o = ng(norm(open(srcs[0], encoding="utf-8").read()), N)
        c = ng(norm(open(f, encoding="utf-8").read()), N)
        leak = len(c & o) / max(len(c), 1) * 100
        t = ng(re.sub(r"\s", "", str(d.get("thesis", ""))), N)
        tleak = len(t & o) / max(len(t), 1) * 100
        if leak >= 5: problems.append(f"漏洩 {leak:.1f}%")
        if tleak > 0: problems.append(f"thesis に原文の言い回し {tleak:.0f}%")
    else:
        problems.append("原文が見つからない")
    ops = sum(1 for p in pts if p.get("kind") == "opinion")
    thesis = str(d.get("thesis", "")).replace("\n", " ")
    print(f"{no} {len(pts):3d} {ops:2d} {leak:5.1f} {tleak:11.0f} {thesis[:60]}")
    if problems:
        bad += 1
        for p in problems: print(f"     ! {p}")
print(f"\n問題あり: {bad} 本")
sys.exit(1 if bad else 0)
