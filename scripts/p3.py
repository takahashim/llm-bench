import json,urllib.request,time,sys
SRC=open('src_text.txt').read()
PROMPTS=[
 ("長文要約", "次の文章を200字程度の日本語で要約してください。\n\n---\n"+SRC+"\n---"),
 ("コード生成","RubyでLRUキャッシュを実装してください。capacityを指定でき、get(key)とput(key,value)を持ちます。minitestのテストも付けてください。"),
 ("多段推論","A、B、C、Dの4人が1列に並びます。次の条件をすべて満たす並び順を、すべて列挙してください。\n条件1: AはBより前\n条件2: CはDより後ろ\n条件3: BはCより前"),
]
def post(url,data):
    r=urllib.request.Request(url,json.dumps(data).encode(),{'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(r,timeout=2400))
B=[]
for n,p in PROMPTS:
    t=time.time()
    d=post('http://127.0.0.1:11434/api/chat',{'model':'qwen3:30b-a3b','messages':[{'role':'user','content':p}],
      'stream':False,'options':{'temperature':0.7,'num_predict':8000,'num_ctx':16384}})
    el=time.time()-t; m=d['message']
    B.append({'q':n,'tok':d['eval_count'],'sec':el,'think':len(m.get('thinking') or ''),'ans':(m['content'] or '').strip(),
              'tps':d['eval_count']/(d['eval_duration']/1e9)})
    print(f"qwen3 {n:<10} {d['eval_count']:>5} tok / {el:>6.1f}s 思考{B[-1]['think']:>5}字 {B[-1]['tps']:.1f} tok/s"); sys.stdout.flush()
json.dump(B,open('heavy_qwen3.json','w'),ensure_ascii=False,indent=1)
