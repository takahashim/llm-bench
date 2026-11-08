# /// script
# requires-python = ">=3.10"
# dependencies = ["unsloth", "pyyaml"]
# ///
"""評価用 10 本の要点から本文を生成する。LoRA 版と、同じ base の few-shot 版(対照)。

    python generate.py --adapter out/swallow-lora --out candidates/lora
    python generate.py --fewshot --out candidates/fewshot      (adapter 無し。手本 3 本を prompt に入れる)

出力は NN.md。評価は phase-1/rate/form.md と同じ 4 段階 + 主張の強弱(SPEC 5 節)。
"""
import argparse, glob, json, os
p = argparse.ArgumentParser()
p.add_argument("--model", default="tokyotech-llm/Llama-3.1-Swallow-8B-Instruct-v0.5")
p.add_argument("--adapter", default=None)
p.add_argument("--fewshot", action="store_true")
p.add_argument("--data", default="data")
p.add_argument("--out", required=True)
p.add_argument("--max_new", type=int, default=3000)
p.add_argument("--push_dataset", default=None, help="候補を上げる dataset repo(HF Jobs で回すとき)")
p.add_argument("--label", default=None, help="push 先のディレクトリ名(既定: --out の basename)")
a = p.parse_args()

from unsloth import FastLanguageModel
import torch
model, tok = FastLanguageModel.from_pretrained(a.adapter or a.model, max_seq_length=16384, load_in_4bit=True)
FastLanguageModel.for_inference(model)

shots = []
if a.fewshot:
    # 学習データのうち短めの 3 本を手本に。LoRA 側はこれらを学習で見ているので、対照として公平
    rows = [json.loads(l) for l in open(f"{a.data}/train.jsonl", encoding="utf-8")]
    rows.sort(key=lambda r: len(r["messages"][2]["content"]))
    shots = [m for r in rows[2:5] for m in r["messages"][1:]]

os.makedirs(a.out, exist_ok=True)
for line in open(f"{a.data}/eval.jsonl", encoding="utf-8"):
    r = json.loads(line)
    msgs = [r["messages"][0]] + shots + [r["messages"][1]]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(ids, max_new_tokens=a.max_new, do_sample=True, temperature=0.7, top_p=0.9,
                             repetition_penalty=1.05, pad_token_id=tok.eos_token_id)
    text = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()
    open(os.path.join(a.out, f"{r['id']}.md"), "w", encoding="utf-8").write(f"# {r['title']}\n\n{text}\n")
    print(r["id"], len(text), "字")

if a.push_dataset:
    from huggingface_hub import HfApi
    HfApi().upload_folder(folder_path=a.out, repo_id=a.push_dataset, repo_type="dataset",
                          path_in_repo=f"candidates/{a.label or os.path.basename(a.out.rstrip('/'))}")
    print("pushed to", a.push_dataset)
