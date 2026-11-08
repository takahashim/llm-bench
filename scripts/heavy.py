import json,urllib.request,time,sys,subprocess,os
SRC=open('src_text.txt').read()
PROMPTS=[
 ("長文要約", "次の文章を200字程度の日本語で要約してください。\n\n---\n"+SRC+"\n---"),
 ("コード生成","RubyでLRUキャッシュを実装してください。capacityを指定でき、get(key)とput(key,value)を持ちます。minitestのテストも付けてください。"),
 ("多段推論","A、B、C、Dの4人が1列に並びます。次の条件をすべて満たす並び順を、すべて列挙してください。\n条件1: AはBより前\n条件2: CはDより後ろ\n条件3: BはCより前"),
]
def post(url,data):
    r=urllib.request.Request(url,json.dumps(data).encode(),{'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(r,timeout=1800))
def wait(url):
    for _ in range(300):
        try:
            urllib.request.urlopen(url,timeout=3); return True
        except Exception: time.sleep(2)
    return False

# --- phase 1: llm-jp ---
post('http://127.0.0.1:11434/api/generate',{'model':'qwen3:30b-a3b','keep_alive':0})
time.sleep(2)
subprocess.Popen('setsid nohup sg render -c "./llama.cpp/build/bin/llama-server -m '+os.path.abspath('llmjp/llm-jp-4.1-32b-a3b-thinking-Q4_K_M.gguf')+' -ngl 99 -c 16384 --jinja --host 127.0.0.1 --port 8099" > srv2.log 2>&1 < /dev/null &',shell=True)
assert wait('http://127.0.0.1:8099/health'), 'llm-jp server did not start'
A=[]
for n,p in PROMPTS:
    t=time.time()
    d=post('http://127.0.0.1:8099/v1/chat/completions',{'messages':[{'role':'user','content':p}],'max_tokens':8000,'temperature':0.7})
    el=time.time()-t; u=d['usage']; m=d['choices'][0]['message']
    A.append({'q':n,'tok':u['completion_tokens'],'sec':el,'think':len(m.get('reasoning_content') or ''),'ans':(m['content'] or '').strip()})
    print(f"llm-jp {n:<10} {u['completion_tokens']:>5} tok / {el:>6.1f}s 思考{A[-1]['think']:>5}字"); sys.stdout.flush()
json.dump(A,open('heavy_llmjp.json','w'),ensure_ascii=False,indent=1)
subprocess.run("pkill -f 'build/bin/llama-server.*8099'",shell=True); time.sleep(4)

# --- phase 2: qwen3 ---
B=[]
for n,p in PROMPTS:
    t=time.time()
    d=post('http://127.0.0.1:11434/api/chat',{'model':'qwen3:30b-a3b','messages':[{'role':'user','content':p}],
      'stream':False,'options':{'temperature':0.7,'num_predict':8000,'num_ctx':16384}})
    el=time.time()-t; m=d['message']
    B.append({'q':n,'tok':d['eval_count'],'sec':el,'think':len(m.get('thinking') or ''),'ans':(m['content'] or '').strip(),
              'tps':d['eval_count']/(d['eval_duration']/1e9)})
    print(f"qwen3  {n:<10} {d['eval_count']:>5} tok / {el:>6.1f}s 思考{B[-1]['think']:>5}字 {B[-1]['tps']:.1f} tok/s"); sys.stdout.flush()
json.dump(B,open('heavy_qwen3.json','w'),ensure_ascii=False,indent=1)
print('\n=== まとめ ===')
ta=tb=sa=sb=0
for x,y in zip(A,B):
    print(f'{x["q"]:<10} llm-jp {x["tok"]:>5}tok/{x["sec"]:>6.1f}s   qwen3 {y["tok"]:>5}tok/{y["sec"]:>6.1f}s   比 {y["tok"]/x["tok"]:.1f}x')
    ta+=x['tok']; tb+=y['tok']; sa+=x['sec']; sb+=y['sec']
print(f'合計       llm-jp {ta:>5}tok/{sa:>6.1f}s   qwen3 {tb:>5}tok/{sb:>6.1f}s   比 {tb/ta:.1f}x / 実時間 {sb/sa:.1f}x')
