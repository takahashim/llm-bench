#!/usr/bin/env python3
"""Phase 0a/0b: bear1 の CPU で bf16 LoRA を当てる(unsloth 版 train.py の CPU 版)。

    phase-0/.venv/bin/python phase-0/train_cpu.py --model phase-0/models/swallow-8b-v0.5 --out phase-0/out/swallow-lora

4bit にしない。8B の bf16 は 16GB で 64GB に載るし、量子化誤差を持ち込まない方が素直。
loss は assistant(本文)だけ。prompt(要点)の書き方は学習させない。
Zen4 の AVX-512 BF16 で bf16 行列積は fp32 の 2.4 倍(実測 1.7 TFLOPS)。
"""
import argparse, json, math, os, time
p = argparse.ArgumentParser()
p.add_argument("--model", required=True)
p.add_argument("--data", default=os.path.join(os.path.dirname(__file__), "data"))
p.add_argument("--out", required=True)
p.add_argument("--max_seq", type=int, default=8192)
p.add_argument("--rank", type=int, default=16)
p.add_argument("--epochs", type=int, default=3)
p.add_argument("--lr", type=float, default=2e-4)
p.add_argument("--accum", type=int, default=8)
p.add_argument("--threads", type=int, default=8)
p.add_argument("--limit", type=int, default=0, help="先頭 N 本だけ(煙テスト用)")
p.add_argument("--no_ckpt", action="store_true", help="gradient checkpointing を切る(小モデルの試験用)")
a = p.parse_args()

import torch
torch.set_num_threads(a.threads)
torch.manual_seed(42)
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model

tok = AutoTokenizer.from_pretrained(a.model, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16, attn_implementation="sdpa",
                                             trust_remote_code=True)
if not a.no_ckpt:
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
model = get_peft_model(model, LoraConfig(
    r=a.rank, lora_alpha=a.rank * 2, lora_dropout=0.0, bias="none", task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]))
model.print_trainable_parameters()


def encode(rows):
    """messages → input_ids と labels。assistant の本文以外は -100。"""
    out = []
    for r in rows:
        msgs = r["messages"]
        prompt_ids = tok.apply_chat_template(msgs[:-1], add_generation_prompt=True, tokenize=True)
        full_ids = tok.apply_chat_template(msgs, tokenize=True)
        if hasattr(prompt_ids, "keys"): prompt_ids = prompt_ids["input_ids"]
        if hasattr(full_ids, "keys"): full_ids = full_ids["input_ids"]
        assert full_ids[:len(prompt_ids)] == prompt_ids, "chat template が prompt の接頭辞を保たない"
        labels = [-100] * len(prompt_ids) + full_ids[len(prompt_ids):]
        if len(full_ids) > a.max_seq:
            # 末尾(本文の後ろ)を切る。prompt が max_seq を食い尽くすと本文が残らないので、その対は捨てる
            full_ids, labels = full_ids[:a.max_seq], labels[:a.max_seq]
        n_label = sum(1 for t in labels if t != -100)
        if n_label < 32:
            print(f"skip {r['id']}: 本文のトークンが {n_label} しか残らない(prompt {len(prompt_ids)} tok)", flush=True)
            continue
        out.append((r["id"], torch.tensor([full_ids]), torch.tensor([labels])))
    return out


def load(name):
    rows = [json.loads(l) for l in open(os.path.join(a.data, f"{name}.jsonl"), encoding="utf-8")]
    return rows[:a.limit] if a.limit else rows


train, val = encode(load("train")), encode(load("val"))
lens = [x.shape[1] for _, x, _ in train]
print(f"train {len(train)} 本: token 長 min {min(lens)} / median {sorted(lens)[len(lens)//2]} / max {max(lens)}, "
      f"合計 {sum(lens):,} tok/epoch; {sum(l >= a.max_seq for l in lens)} 本が max_seq で切られた", flush=True)


@torch.no_grad()
def evaluate():
    model.eval(); tot = n = 0
    for _, x, y in val:
        out = model(input_ids=x, labels=y); k = int((y != -100).sum())
        tot += float(out.loss) * k; n += k
    model.train(); return tot / max(n, 1)


params = [q for q in model.parameters() if q.requires_grad]
opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.0, betas=(0.9, 0.999))
steps_total = math.ceil(len(train) / a.accum) * a.epochs
warm = max(1, round(steps_total * 0.1))
sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / warm) *
                                          (0.5 * (1 + math.cos(math.pi * max(0, s - warm) / max(1, steps_total - warm)))))
os.makedirs(a.out, exist_ok=True)
log = open(os.path.join(a.out, "log.jsonl"), "a", encoding="utf-8")
def note(**kw):
    kw["t"] = round(time.time() - t0, 1); print(kw, flush=True); log.write(json.dumps(kw, ensure_ascii=False) + "\n"); log.flush()

t0 = time.time()
note(event="val", epoch=0, val_loss=round(evaluate(), 4))
model.train(); step = 0; g = torch.Generator().manual_seed(42); t_step = time.time()
for ep in range(1, a.epochs + 1):
    order = torch.randperm(len(train), generator=g).tolist()
    for i in range(0, len(order), a.accum):
        chunk = order[i:i + a.accum]; ntok = max(1, sum(int((train[j][2] != -100).sum()) for j in chunk)); acc = 0.0
        for j in chunk:
            _, x, y = train[j]
            out = model(input_ids=x, labels=y)
            # 本文トークン数で重み付け(長い記事を 1 本として軽く扱わない)
            loss = out.loss * int((y != -100).sum()) / ntok
            loss.backward(); acc += float(loss.detach())
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step(); sched.step(); opt.zero_grad(set_to_none=True); step += 1
        now = time.time()
        note(event="step", step=step, of=steps_total, epoch=ep, loss=round(acc, 4), lr=round(sched.get_last_lr()[0], 6),
             tok=ntok, tok_per_s=round(sum(train[j][1].shape[1] for j in chunk) / (now - t_step), 1))
        t_step = now
    note(event="val", epoch=ep, val_loss=round(evaluate(), 4))
    model.save_pretrained(a.out); tok.save_pretrained(a.out)
json.dump(vars(a), open(os.path.join(a.out, "train_args.json"), "w"), ensure_ascii=False, indent=1)
note(event="done", out=a.out)
