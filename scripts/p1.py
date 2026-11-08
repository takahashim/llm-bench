import json,urllib.request,time,sys
PROMPTS=[
 ("敬語の簡潔化","次の文を、意味を変えずに、より自然で簡潔な日本語に直してください。理由も一行で。\n\n「本システムにおきましては、ユーザー様がログインを実施された際に、認証情報の検証処理が行われることとなっております。」"),
 ("用語の説明","「冪等性」をソフトウェア開発の文脈で、具体例を1つ挙げて3文以内で説明してください。"),
 ("簡単な計算","りんごが5個あります。3個食べて、その後2個買いました。今いくつありますか。簡潔に答えてください。"),
 ("コード説明","Rubyの `Enumerable#each_with_object` と `#inject` の使い分けを、2文で説明してください。"),
]
def post(url,data):
    r=urllib.request.Request(url,json.dumps(data).encode(),{'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(r,timeout=900))
out=[]
for name,p in PROMPTS:
    t=time.time()
    d=post('http://127.0.0.1:8099/v1/chat/completions',
      {'messages':[{'role':'user','content':p}],'max_tokens':4000,'temperature':0.7})
    el=time.time()-t; u=d['usage']; m=d['choices'][0]['message']
    out.append({'q':name,'tok':u['completion_tokens'],'sec':el,
                'think':len(m.get('reasoning_content') or ''),'ans':(m['content'] or '').strip()})
    print(f"{name:<14} {u['completion_tokens']:>5} tok / {el:>6.1f}s  思考{len(m.get('reasoning_content') or ''):>5}字"); sys.stdout.flush()
json.dump(out,open('llmjp.json','w'),ensure_ascii=False,indent=1)
