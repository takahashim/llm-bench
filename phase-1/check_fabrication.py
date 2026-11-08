#!/usr/bin/env python3
"""候補の数値・英数字トークンが facts に存在するかを検査する（仕様4節の捏造検査）。
usage: check_fabrication.py [candidates_dir] [facts_dir]"""
import re,json,glob,os,sys
B=os.path.dirname(os.path.abspath(__file__))
def toks(t):
    t=re.sub(r'\[コード\]','',t)
    nums=set(re.findall(r'\d+(?:\.\d+)?',t))
    words=set(w for w in re.findall(r'[A-Za-z][A-Za-z0-9_.:/\-]{2,}',t))
    return nums,words
tot_bad=0
CD=sys.argv[1] if len(sys.argv)>1 else 'candidates'; FD=sys.argv[2] if len(sys.argv)>2 else 'facts'
for f in sorted(glob.glob(f'{B}/{CD}/*.md')):
    n=os.path.basename(f)[:2]
    facts=open(f'{B}/{FD}/{n}.yaml').read()
    fn,fw=toks(facts); cn,cw=toks(open(f).read())
    bad_n=sorted(cn-fn, key=lambda x:(len(x),x)); bad_w=sorted(cw-fw)
    # 年号・版数のような自明な派生は除外しない。すべて列挙して人が見る
    tot_bad+=len(bad_n)+len(bad_w)
    flag='clean' if not (bad_n or bad_w) else f'数値{len(bad_n)} 語{len(bad_w)}'
    print(f'{n}  {flag}')
    for x in bad_n[:6]: print(f'      数値: {x}')
    for x in bad_w[:8]: print(f'      語  : {x}')
print(f'\n要確認トークン 合計 {tot_bad}')
