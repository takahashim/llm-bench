#!/usr/bin/env python3
"""judge.md と key.json を突き合わせて集計する。"""
import json,re,os
B=os.path.dirname(os.path.abspath(__file__))
key=json.load(open(f'{B}/pairs/key.json'))
rows=re.findall(r'^\|\s*(\d\d)\s*\|\s*([AB])\s*\|\s*(.*?)\s*\|$',open(f'{B}/pairs/judge.md').read(),re.M)
cand=orig=0
for n,pick,why in rows:
    who=key[n][pick]; cand+=who=='candidate'; orig+=who=='original'
    print(f'{n}  選択={pick} → {who:<9}  {why}')
tot=cand+orig
print(f'\n候補が選ばれた: {cand}/{tot}  原文: {orig}/{tot}')
if tot: print('合格ライン(70%):', '達成' if cand/tot>=0.7 else '未達')
