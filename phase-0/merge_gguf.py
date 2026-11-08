#!/usr/bin/env python3
"""adapter を base に merge して GGUF にする(bear1 の llama-server で生成するため)。

    phase-0/.venv/bin/python phase-0/merge_gguf.py --model phase-0/models/swallow-8b-v0.5 \
        --adapter phase-0/out/swallow-lora --out phase-0/out/swallow-lora.Q8_0.gguf
    phase-0/.venv/bin/python phase-0/merge_gguf.py --model phase-0/models/swallow-8b-v0.5 \
        --out phase-0/out/swallow-base.Q8_0.gguf            # adapter 無し = few-shot 対照用の base

Q8_0 にするのは、量子化の誤差で LoRA の差が見えなくなるのを避けるため。
LoRA 版も base も同じ経路で作るので、比較の土俵は同じ。
"""
import argparse, os, shutil, subprocess, sys, tempfile
p = argparse.ArgumentParser()
p.add_argument("--model", required=True)
p.add_argument("--adapter", default=None)
p.add_argument("--out", required=True)
p.add_argument("--quant", default="Q8_0")
p.add_argument("--llama_cpp", default=os.path.expanduser("~/git/llama.cpp"))
p.add_argument("--bin", default=os.path.expanduser("~/bin/llama.cpp"))
a = p.parse_args()

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

work = tempfile.mkdtemp(prefix="merge-", dir=os.path.dirname(os.path.abspath(a.out)))
try:
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16, trust_remote_code=True)
    if a.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, a.adapter).merge_and_unload()
        print("merged", a.adapter, flush=True)
    model.save_pretrained(work, safe_serialization=True)
    AutoTokenizer.from_pretrained(a.model, trust_remote_code=True).save_pretrained(work)
    # llm-jp のようにトークナイザの python を同梱するモデルは、その .py も要る
    for f in os.listdir(a.model):
        if f.endswith(".py") or f in ("tokenizer.model",):
            shutil.copy(os.path.join(a.model, f), work)
    del model
    bf16 = os.path.join(work, "model.bf16.gguf")
    # 変換スクリプトと同じ版の gguf-py を使う(pip の gguf と食い違うことがある)
    env = dict(os.environ, PYTHONPATH=os.path.join(a.llama_cpp, "gguf-py"), LD_LIBRARY_PATH=a.bin)
    subprocess.run([sys.executable, os.path.join(a.llama_cpp, "convert_hf_to_gguf.py"), work,
                    "--outfile", bf16, "--outtype", "bf16"], check=True, env=env)
    subprocess.run([os.path.join(a.bin, "llama-quantize"), bf16, a.out, a.quant], check=True, env=env)
    print("wrote", a.out, f"{os.path.getsize(a.out) / 2**30:.2f} GiB")
finally:
    shutil.rmtree(work, ignore_errors=True)
