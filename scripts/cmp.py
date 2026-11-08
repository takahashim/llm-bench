import json,urllib.request,time,sys
PROMPTS=[
 ("敬語の簡潔化","次の文を、意味を変えずに、より自然で簡潔な日本語に直してください。理由も一行で。\n\n「本システムにおきましては、ユーザー様がログインを実施された際に、認証情報の検証処理が行われることとなっております。」"),
 ("用語の説明","「冪等性」をソフトウェア開発の文脈で、具体例を1つ挙げて3文以内で説明してください。"),
 ("簡単な計算","りんごが5個あります。3個食べて、その後2個買いました。今いくつありますか。簡潔に答えてください。"),
 ("コード説明","Rubyの `Enumerable#each_with_object` と `#inject` の使い分けを、2文で説明してください。"),
]
def post(url,data,timeout=600):
    r=urllib.request.Request(url,json.dumps(data).encode(),{'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(r,timeout=timeout))
rows=[]
for name,p in PROMPTS:
    # llm-jp (llama-server)
    t=time.time()
    d=post('http://127.0.0.1:8099/v1/chat/completions',
      {'messages':[{'role':'user','content':p}],'max_tokens':4000,'temperature':0.7})
    el=time.time()-t; u=d['usage']; m=d['choices'][0]['message']
    a=(u['completion_tokens'], el, len(m.get('reasoning_content') or ''), (m['content'] or '').strip())
    # qwen3 (ollama)
    t=time.time()
    d=post('http://127.0.0.1:11434/api/chat',
      {'model':'qwen3:30b-a3b','messages':[{'role':'user','content':p}],'stream':False,
       'options':{'temperature':0.7,'num_predict':4000}})
    el=time.time()-t; m=d['message']
    b=(d['eval_count'], el, len(m.get('thinking') or ''), (m['content'] or '').strip())
    rows.append((name,a,b))
    print(f'--- {name} ---')
    print(f'  llm-jp : {a[0]:>5} tok / {a[1]:>6.1f}s  思考{a[2]:>5}字')
    print(f'  qwen3  : {b[0]:>5} tok / {b[1]:>6.1f}s  思考{b[2]:>5}字')
    sys.stdout.flush()
print()
print(f'{"":14}{"llm-jp tok":>12}{"qwen3 tok":>11}{"llm-jp s":>10}{"qwen3 s":>9}')
ta=tb=sa=sb=0
for n,a,b in rows:
    print(f'{n:<14}{a[0]:>12}{b[0]:>11}{a[1]:>10.1f}{b[1]:>9.1f}')
    ta+=a[0]; tb+=b[0]; sa+=a[1]; sb+=b[1]
print(f'{"合計":<13}{ta:>12}{tb:>11}{sa:>10.1f}{sb:>9.1f}')
print(f'\nトークン比 qwen3/llm-jp = {tb/ta:.1f}x   実時間比 = {sb/sa:.1f}x')
json.dump([{ 'q':n,'llmjp':a,'qwen3':b} for n,a,b in rows],open('cmp.json','w'),ensure_ascii=False,indent=1)
