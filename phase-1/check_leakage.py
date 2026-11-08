#!/usr/bin/env python3
"""原文の言い回しが事実リスト・候補にどれだけ漏れているかを文字n-gramで測る。
usage: check_leakage.py <原文.md> <比較対象...>"""
import re,sys
def norm(t):
    t=re.sub(r'```.*?```','',t,flags=re.S); t=re.sub(r'\[コード\]','',t)
    t=re.sub(r'https?://\S+','',t); t=re.sub(r'^#+ .*$','',t,flags=re.M)
    t=re.sub(r'^\s*(id|kind|scope|source|title|reader|points|facts):.*$','',t,flags=re.M)
    return re.sub(r'\s','',t)
def ng(t,n): return {t[i:i+n] for i in range(len(t)-n+1)}
N=10
o=ng(norm(open(sys.argv[1]).read()),N)
for f in sys.argv[2:]:
    c=ng(norm(open(f).read()),N)
    print(f'{f}: {len(c&o)/max(len(c),1)*100:5.1f}%  ({len(c&o)}/{len(c)} の{N}-gramが原文に存在)')
