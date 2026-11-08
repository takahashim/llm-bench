# -*- coding: utf-8 -*-
"""humanizer-ja / imoz の指標のうち機械判定できるものを検査する。
判断を要する項目（handleの質・段落の一話題性・三つ組の強制）は対象外。"""
import json,re,os
B=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def sentences(a):
    a=re.sub(r'```.*?```','',a,flags=re.S)          # コードブロックは除外
    a=re.sub(r'^#+ .*$','',a,flags=re.M)            # 見出しも除外
    return [s.strip() for s in re.split(r'[。\n]',a) if s.strip()]

def check(a):
    h=[]; S=sentences(a); body=''.join(S)
    heads=len(re.findall(r'^#+ ',a,re.M))
    if heads and len(a)/heads < 200: h.append(('見出し過多',heads))
    n=len(re.findall(r'^\s*[-*]\s*\*\*[^*]+\*\*[::。]',a,re.M))
    if n: h.append(('太字+コロンの箇条書き',n))
    n=len(re.findall(r'——|—',a))
    if n>1: h.append(('em-dash',n))
    n=len(re.findall(r'ではな[いく]|のではなく|ではありません|とは限らない',body))
    if n: h.append(('否定の対構文',n))
    n=sum(1 for s in S if re.match(r'(また|さらに|そのため|したがって|つまり|一方|しかし|ただし|なお)',s))
    if n>3: h.append(('文頭の接続詞',n))
    n=len(re.findall(r'非常に|極めて|きわめて|不可欠|最も重要|本質的',body))
    if n>1: h.append(('意義の過剰強調',n))
    n=len(re.findall(r'と言えるでしょう|と言えます|注目に値|重要な(ポイント|点)|留意',body))
    if n: h.append(('定型の評価句',n))
    n=len(re.findall(r'一般的に|とされて(いま|い)す|と言われ|考えられています',body))
    if n: h.append(('曖昧な出典',n))
    n=len(re.findall(r'することができ(ます|る)',body))
    if n: h.append(('することができます',n))
    n=len(re.findall(r'の(促進|向上|実施|改善|強化|最適化|活用)',body))
    if n: h.append(('抽象名詞構文',n))
    if re.match(r'(近年|昨今|現代|今日|一般に)',S[0] if S else ''): h.append(('一般論で始まる',1))
    if S and re.search(r'(説明|解説|紹介)し(ま|よ)',S[0]): h.append(('予告で始まる',1))
    # 敬体/常体の混在
    des=sum(1 for s in S if re.search(r'(です|ます|ません|でしょう)$',s))
    dea=sum(1 for s in S if re.search(r'(である|だ|した|ない|いる|なる|る)$',s))
    if des and dea and min(des,dea)/(des+dea) > 0.15: h.append(('敬体と常体の混在',f'{des}/{dea}'))
    # カタカナ率
    k=len(re.findall(r'[ァ-ヴー]',body))
    if body and k/len(body) > 0.18: h.append(('カタカナ率',f'{k/len(body)*100:.0f}%'))
    # 文長
    if S:
        avg=sum(len(s) for s in S)/len(S)
        if avg>55: h.append(('平均文長',f'{avg:.0f}字'))
    return h

sets=[('Opus',['results/gen_opus.json','results/gen_opus2.json']),
      ('llm-jp32B',['results/gen_llmjp.json']),
      ('qwen3-30B',['results/gen_qwen3.json'])]
tot={}
for lbl,fs in sets:
    print(f'\n{"="*66}\n{lbl}\n{"="*66}')
    for f in fs:
        try: d=json.load(open(f'{B}/{f}'))
        except: continue
        for r in d:
            hits=check(r['ans'])
            print(f"  {r['q']:<10}{len(r['ans']):>5}字  " + ('clean' if not hits else ' / '.join(f'{n}({c})' for n,c in hits)))
            for n,_ in hits: tot[n]=tot.get(n,0)+1
print(f'\n{"="*66}\n指標ごとの該当本数（全16本）\n{"="*66}')
for k,v in sorted(tot.items(),key=lambda x:-x[1]): print(f'  {k:<24}{v:>3}本')
