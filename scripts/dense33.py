import json,urllib.request,time,sys,os
B=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC=open(f'{B}/data/src_text.txt').read()
PROMPTS=[
 ("敬語の簡潔化","次の文を、意味を変えずに、より自然で簡潔な日本語に直してください。理由も一行で。\n\n「本システムにおきましては、ユーザー様がログインを実施された際に、認証情報の検証処理が行われることとなっております。」"),
 ("用語の説明","「冪等性」をソフトウェア開発の文脈で、具体例を1つ挙げて3文以内で説明してください。"),
 ("簡単な計算","りんごが5個あります。3個食べて、その後2個買いました。今いくつありますか。簡潔に答えてください。"),
 ("コード説明","Rubyの `Enumerable#each_with_object` と `#inject` の使い分けを、2文で説明してください。"),
 ("長文要約","次の文章を200字程度の日本語で要約してください。\n\n---\n"+SRC+"\n---"),
 ("コード生成","RubyでLRUキャッシュを実装してください。capacityを指定でき、get(key)とput(key,value)を持ちます。minitestのテストも付けてください。"),
 ("多段推論","A、B、C、Dの4人が1列に並びます。次の条件をすべて満たす並び順を、すべて列挙してください。\n条件1: AはBより前\n条件2: CはDより後ろ\n条件3: BはCより前"),
]
def post(d):
    r=urllib.request.Request('http://127.0.0.1:8099/v1/chat/completions',json.dumps(d).encode(),{'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(r,timeout=3600))
out=[]
for n,p in PROMPTS:
    t=time.time()
    d=post({'messages':[{'role':'user','content':p}],'max_tokens':8000,'temperature':0.7})
    el=time.time()-t; u=d['usage']; m=d['choices'][0]['message']
    out.append({'q':n,'tok':u['completion_tokens'],'sec':el,
                'think':len(m.get('reasoning_content') or ''),'ans':(m['content'] or '').strip()})
    print(f"{n:<12} {u['completion_tokens']:>5} tok / {el:>7.1f}s  思考{out[-1]['think']:>5}字"); sys.stdout.flush()
    json.dump(out,open(f'{B}/results/dense33.json','w'),ensure_ascii=False,indent=1)
