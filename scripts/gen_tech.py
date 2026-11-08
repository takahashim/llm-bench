import json,urllib.request,time,sys,os
B=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS=[
 ("概念説明","MoE（Mixture of Experts）モデルが、同じパラメータ数のdenseモデルより推論が速い理由を説明してください。読者はソフトウェアエンジニアですが、LLMの内部構造には詳しくありません。600字程度。"),
 ("原因切り分け","ollamaでローカルLLMを動かしたところ、GPUが搭載されているのにCPUで実行されてしまいます。原因の切り分け方を説明してください。読者はLinuxは使えるがLLM実行環境には不慣れです。600字程度。"),
 ("比較と推奨","ローカルでLLMを動かすPCを選ぶとき、メモリ帯域とメモリ容量のどちらを優先すべきかを説明してください。読者は予算を決めて機種を選ぼうとしています。600字程度。"),
]
def post(url,data):
    r=urllib.request.Request(url,json.dumps(data).encode(),{'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(r,timeout=1800))
which=sys.argv[1]
out=[]
for n,p in PROMPTS:
    t=time.time()
    if which=='llmjp':
        d=post('http://127.0.0.1:8099/v1/chat/completions',{'messages':[{'role':'user','content':p}],'max_tokens':6000,'temperature':0.7})
        tok=d['usage']['completion_tokens']; m=d['choices'][0]['message']
        think=len(m.get('reasoning_content') or ''); ans=(m['content'] or '').strip()
    else:
        d=post('http://127.0.0.1:11434/api/chat',{'model':'qwen3:30b-a3b','messages':[{'role':'user','content':p}],
               'stream':False,'options':{'temperature':0.7,'num_predict':6000}})
        tok=d['eval_count']; m=d['message']
        think=len(m.get('thinking') or ''); ans=(m['content'] or '').strip()
    el=time.time()-t
    out.append({'q':n,'tok':tok,'sec':el,'think':think,'ans':ans})
    print(f"{which:<6} {n:<8} {tok:>5} tok / {el:>6.1f}s 思考{think:>5}字 本文{len(ans):>4}字"); sys.stdout.flush()
    json.dump(out,open(f'{B}/results/gen_{which}.json','w'),ensure_ascii=False,indent=1)
