#!/usr/bin/env python3
"""原文と候補をブラインドで並べる。
各ペアで A/B のどちらが原文かはランダム。対応表は pairs/key.json に書き出し、
判定が終わるまで見ないこと。"""
import json,random,os,sys
B=os.path.dirname(os.path.abspath(__file__))
sel=json.load(open(f'{B}/selection.json'))['eval']
random.seed(int(sys.argv[1]) if len(sys.argv)>1 else 20261108)
key={}
for e in sel:
    n=f"{e['n']:02d}"
    orig=open(f"{B}/texts/eval/{n}.md").read().strip()
    cand_f=f"{B}/candidates/{n}.md"
    if not os.path.exists(cand_f): print(f'skip {n}: candidate なし'); continue
    cand=open(cand_f).read().strip()
    orig_is_A=random.random()<0.5
    A,Bt=(orig,cand) if orig_is_A else (cand,orig)
    key[n]={'A':'original' if orig_is_A else 'candidate','B':'candidate' if orig_is_A else 'original'}
    with open(f"{B}/pairs/{n}.md",'w') as f:
        f.write(f"# ペア {n}: {e['title']}\n\n")
        f.write("どちらが「自分が書いたものに近いか」を選び、理由を一言。\n\n")
        f.write("---\n\n## A\n\n"+A+"\n\n---\n\n## B\n\n"+Bt+"\n")
json.dump(key,open(f'{B}/pairs/key.json','w'),indent=1)
with open(f'{B}/pairs/judge.md','w') as f:
    f.write("# 判定記録\n\n各ペアを読み、A/B のどちらが自分の文章に近いかと理由を記入。\n")
    f.write("**key.json は全て記入し終えるまで開かないこと。**\n\n")
    f.write("| ペア | 選択(A/B) | 理由 |\n|---|---|---|\n")
    for n in key: f.write(f"| {n} | | |\n")
print(f'ペア {len(key)}件を pairs/ に書き出し。対応表は pairs/key.json')
