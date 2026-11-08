#!/usr/bin/env python3
"""rate/form.md の4段階評価を集計する。"""
import re,os
B=os.path.dirname(os.path.abspath(__file__))
rows=re.findall(r'^\|\s*(\d\d)\s*\|\s*([ABCD])\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$',open(f'{B}/rate/form.md').read(),re.M)
if not rows: print('未記入'); raise SystemExit
from collections import Counter
c=Counter(g for _,g,_,_ in rows)
print(f'{"候補":<5}{"評価":<5}{"問題":<8}一言')
for n,g,kind,why in rows: print(f'{n:<5}{g:<5}{kind:<8}{why}')
ok=c['A']+c['B']
print(f'\nA={c["A"]} B={c["B"]} C={c["C"]} D={c["D"]}  → A+B = {ok}/{len(rows)}')
print('合格ライン(7本):', '達成' if ok>=7 else '未達')
tmpl=[r for r in rows if r[0] in ('01','02','03')]; own=[r for r in rows if r[0] not in ('01','02','03')]
if own:
    ok2=sum(1 for _,g,_,_ in own if g in 'AB')
    print(f'構成を自力で組んだ 04〜10 に限ると: A+B = {ok2}/{len(own)}')
kinds=Counter(k for _,g,k,_ in rows if g in 'CD' and k)
if kinds: print('C/D の問題の内訳:', dict(kinds))
