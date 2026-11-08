# /// script
# requires-python = ">=3.10"
# dependencies = ["unsloth", "trl>=0.15", "datasets", "pyyaml"]
# ///
"""Phase 0a: 著者の記事 33 本で Swallow-8B に QLoRA を当てる。

    python train.py --data data --out out/swallow-lora
    hf jobs uv run phase-0/train.py --flavor a10g-large ...   (クラウドで回す場合。README 参照)

学習データは build_dataset.py が作った data/train.jsonl (messages 形式)。
val.jsonl の loss を epoch ごとに出す。学習後は adapter だけを保存する。
"""
import argparse, json, os
p = argparse.ArgumentParser()
p.add_argument("--model", default="tokyotech-llm/Llama-3.1-Swallow-8B-Instruct-v0.5")
p.add_argument("--data", default="data")
p.add_argument("--out", default="out/swallow-lora")
p.add_argument("--max_seq", type=int, default=8192)
p.add_argument("--rank", type=int, default=16)
p.add_argument("--epochs", type=float, default=3)
p.add_argument("--lr", type=float, default=2e-4)
p.add_argument("--push", default=None, help="学習後に adapter を lora/ として上げる dataset repo (任意)")
a = p.parse_args()

from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig

model, tok = FastLanguageModel.from_pretrained(a.model, max_seq_length=a.max_seq, load_in_4bit=True)
model = FastLanguageModel.get_peft_model(
    model, r=a.rank, lora_alpha=a.rank * 2, lora_dropout=0.0, bias="none",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    use_gradient_checkpointing="unsloth", random_state=42)

ds = load_dataset("json", data_files={"train": f"{a.data}/train.jsonl", "val": f"{a.data}/val.jsonl"})
def to_text(r): return {"text": tok.apply_chat_template(r["messages"], tokenize=False)}
ds = ds.map(to_text, remove_columns=ds["train"].column_names)
lens = [len(tok(t)["input_ids"]) for t in ds["train"]["text"]]
print(f"train {len(lens)} 本, token 長 min {min(lens)} / median {sorted(lens)[len(lens)//2]} / max {max(lens)}; "
      f"{sum(l > a.max_seq for l in lens)} 本が max_seq を超えて切られる")

trainer = SFTTrainer(
    model=model, tokenizer=tok, train_dataset=ds["train"], eval_dataset=ds["val"],
    args=SFTConfig(
        output_dir=a.out, per_device_train_batch_size=1, gradient_accumulation_steps=8,
        num_train_epochs=a.epochs, learning_rate=a.lr, lr_scheduler_type="cosine", warmup_ratio=0.1,
        logging_steps=1, eval_strategy="epoch", save_strategy="no", bf16=True,
        max_seq_length=a.max_seq, dataset_text_field="text", packing=False,
        report_to="none", seed=42))
# 本文(assistant)だけを loss に入れる。prompt を学習させると要点の書き方を覚えてしまう
from unsloth.chat_templates import train_on_responses_only
trainer = train_on_responses_only(trainer,
    instruction_part="<|start_header_id|>user<|end_header_id|>\n\n",
    response_part="<|start_header_id|>assistant<|end_header_id|>\n\n")
print("val loss (before):", trainer.evaluate()["eval_loss"])
trainer.train()
print("val loss (after):", trainer.evaluate()["eval_loss"])
model.save_pretrained(a.out); tok.save_pretrained(a.out)
json.dump(vars(a), open(os.path.join(a.out, "train_args.json"), "w"), ensure_ascii=False, indent=1)
if a.push:
    from huggingface_hub import HfApi
    HfApi().upload_folder(folder_path=a.out, repo_id=a.push, repo_type="dataset", path_in_repo="lora")
    print("pushed lora/ to", a.push)
print("saved", a.out)
