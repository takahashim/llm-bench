#!/usr/bin/env python3
"""評価用 10 本の要点から、bear1 の llama-server(Vulkan)で本文を生成する。

    python3 phase-0/generate_local.py --gguf phase-0/out/swallow-lora.Q8_0.gguf --out phase-0/candidates/lora
    python3 phase-0/generate_local.py --gguf phase-0/out/swallow-base.Q8_0.gguf --fewshot --out phase-0/candidates/fewshot

llama-server を自分で立てて(sg render 経由)、終わったら落とす。依存は標準ライブラリだけ。
few-shot 版は学習データの短い 3 本を手本に入れる(generate.py と同じ選び方)。
"""
import argparse, json, os, subprocess, time, urllib.request
p = argparse.ArgumentParser()
p.add_argument("--gguf", required=True)
p.add_argument("--out", required=True)
p.add_argument("--fewshot", action="store_true")
p.add_argument("--data", default=os.path.join(os.path.dirname(__file__), "data"))
p.add_argument("--port", type=int, default=8098)
p.add_argument("--ctx", type=int, default=16384)
p.add_argument("--max_tokens", type=int, default=3000)
p.add_argument("--temperature", type=float, default=0.7)
p.add_argument("--repeat_penalty", type=float, default=1.05)
p.add_argument("--dry_multiplier", type=float, default=0.0, help="DRY サンプラ(反復抑止)。0.8 程度で効く。0 で無効")
p.add_argument("--bin", default=os.path.expanduser("~/bin/llama.cpp"))
p.add_argument("--extra", default="", help="llama-server に足す引数(例: --jinja --reasoning-budget 0)")
a = p.parse_args()

cmd = (f"LD_LIBRARY_PATH={a.bin} {a.bin}/llama-server -m {a.gguf} -ngl 99 -c {a.ctx} --jinja --flash-attn on "
       f"--host 127.0.0.1 --port {a.port} {a.extra}")
os.makedirs(a.out, exist_ok=True)
srv = subprocess.Popen(["sg", "render", "-c", cmd], stdout=open(a.out + ".server.log", "a"), stderr=subprocess.STDOUT)
url = f"http://127.0.0.1:{a.port}"
for _ in range(600):
    try:
        if urllib.request.urlopen(url + "/health", timeout=2).status == 200: break
    except Exception: time.sleep(1)
else:
    srv.kill(); raise SystemExit("llama-server が起動しない。" + a.out + ".server.log を見る")

shots = []
if a.fewshot:
    rows = [json.loads(l) for l in open(os.path.join(a.data, "train.jsonl"), encoding="utf-8")]
    rows.sort(key=lambda r: len(r["messages"][2]["content"]))
    shots = [m for r in rows[2:5] for m in r["messages"][1:]]

try:
    for line in open(os.path.join(a.data, "eval.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        msgs = [r["messages"][0]] + shots + [r["messages"][1]]
        body = json.dumps({"messages": msgs, "max_tokens": a.max_tokens, "temperature": a.temperature,
                           "top_p": 0.9, "repeat_penalty": a.repeat_penalty, "seed": 42,
                           "dry_multiplier": a.dry_multiplier, "dry_base": 1.75, "dry_allowed_length": 2}).encode()
        t = time.time()
        req = urllib.request.Request(url + "/v1/chat/completions", body, {"Content-Type": "application/json"})
        res = json.load(urllib.request.urlopen(req, timeout=3600))
        msg = res["choices"][0]["message"]
        text = (msg.get("content") or "").strip()
        usage = res.get("usage", {})
        open(os.path.join(a.out, f"{r['id']}.md"), "w", encoding="utf-8").write(f"# {r['title']}\n\n{text}\n")
        extra = f" 思考 {len(msg['reasoning_content'])} 字" if msg.get("reasoning_content") else ""
        print(f"{r['id']} {len(text)} 字 / {usage.get('completion_tokens', '?')} tok / {time.time() - t:.0f}s{extra}", flush=True)
finally:
    srv.terminate()
    try: srv.wait(10)
    except Exception: srv.kill()
