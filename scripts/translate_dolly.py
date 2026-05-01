"""Translate `allenlin316/databricks-dolly-15k-no-safety` to Traditional Chinese.

- Endpoint: https://qwen.pangolin.apmic.ai/v1/chat/completions (Qwen3.6-27B, no-think)
- Concurrency: configurable, defaults to 16
- Resume: appends to JSONL; on rerun, skips ids already present
- Simplified detection: per-character check. If any simplified-only char appears,
  retranslate with a stronger prompt up to N times, then mark `needs_review: true`
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx
from datasets import load_dataset
from dragonmapper import hanzi as H
from tqdm.asyncio import tqdm as atqdm

API_URL = "https://qwen.pangolin.apmic.ai/v1/chat/completions"
MODEL = "Qwen3.6-27B"
SOURCE_DATASET = "allenlin316/databricks-dolly-15k-no-safety"
OUTPUT_DIR = Path("datasets/tw-databricks-dolly-15k-no-safety")
OUTPUT_FILE = OUTPUT_DIR / "datasets.jsonl"

DEFAULT_CONCURRENCY = 16
DEFAULT_MAX_RETRIES_SIMPLIFIED = 3
REQUEST_TIMEOUT = 300.0
MAX_TOKENS = 4096


def has_any_simplified_only(text: str) -> bool:
    if not text:
        return False
    return any(H.identify(ch) is H.SIMPLIFIED for ch in text)


SYSTEM_PROMPT = (
    "你是一位專業的英翻中翻譯員，目標語言為臺灣繁體中文。\n"
    "規則：\n"
    "1. 只輸出翻譯結果，不要任何解釋、前言、引號或其他標記。\n"
    "2. 保留原文中的程式碼、URL、人名、地名、專有名詞、數字格式。\n"
    "3. 使用臺灣慣用的詞彙與用法。\n"
    "4. 嚴禁使用任何簡體字，必須全部使用繁體字。"
)

USER_PROMPT = "請將下列英文翻譯為臺灣繁體中文：\n\n{text}"

RETRY_USER_PROMPT = (
    "你的上次翻譯包含了簡體字，這是不允許的。請重新翻譯，"
    "**絕對不可以使用任何簡體字**，必須全部使用臺灣繁體中文：\n\n{text}"
)


async def call_api(
    client: httpx.AsyncClient, system: str, user: str
) -> str | None:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": MAX_TOKENS,
        "temperature": 0.2,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            r = await client.post(API_URL, json=payload, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            data = r.json()
            content = data["choices"][0]["message"].get("content")
            if content is None:
                return None
            return content.strip()
        except (httpx.HTTPError, KeyError, json.JSONDecodeError) as e:
            last_err = e
            await asyncio.sleep(2 ** attempt)
    raise RuntimeError(f"API call failed after retries: {last_err}")


async def translate_field(
    client: httpx.AsyncClient, text: str, max_retries: int
) -> tuple[str, bool]:
    """Returns (translation, needs_review). Empty input returns ("", False)."""
    if not text or not text.strip():
        return "", False

    user_prompt = USER_PROMPT.format(text=text)
    last_translation = ""
    for attempt in range(max_retries + 1):
        if attempt > 0:
            user_prompt = RETRY_USER_PROMPT.format(text=text)
        translation = await call_api(client, SYSTEM_PROMPT, user_prompt)
        if not translation:
            continue
        last_translation = translation
        if not has_any_simplified_only(translation):
            return translation, False
    return last_translation, True


async def translate_row(
    sem: asyncio.Semaphore,
    client: httpx.AsyncClient,
    row: dict,
    idx: int,
    max_retries: int,
) -> dict:
    async with sem:
        instruction, ins_r = await translate_field(client, row["instruction"], max_retries)
        context, ctx_r = await translate_field(client, row["context"], max_retries)
        response, res_r = await translate_field(client, row["response"], max_retries)
    return {
        "id": idx,
        "instruction": instruction,
        "context": context,
        "response": response,
        "category": row["category"],
        "needs_review": ins_r or ctx_r or res_r,
    }


def load_done_ids(path: Path) -> set[int]:
    if not path.exists():
        return set()
    done: set[int] = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                done.add(json.loads(line)["id"])
            except (json.JSONDecodeError, KeyError):
                pass
    return done


async def run(limit: int | None, concurrency: int, max_retries: int) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Loading {SOURCE_DATASET} ...", file=sys.stderr)
    ds = load_dataset(SOURCE_DATASET, split="train")
    total = len(ds)
    if limit is not None:
        total = min(total, limit)
    print(f"Total rows: {total}", file=sys.stderr)

    done_ids = load_done_ids(OUTPUT_FILE)
    if done_ids:
        print(f"Resume: {len(done_ids)} rows already in {OUTPUT_FILE}", file=sys.stderr)

    pending: list[tuple[int, dict]] = []
    for idx in range(total):
        if idx in done_ids:
            continue
        pending.append((idx, ds[idx]))

    if not pending:
        print("Nothing to do.", file=sys.stderr)
        return

    print(f"Translating {len(pending)} rows with concurrency={concurrency} ...", file=sys.stderr)

    sem = asyncio.Semaphore(concurrency)
    file_lock = asyncio.Lock()
    err_count = 0

    limits = httpx.Limits(max_connections=concurrency * 2, max_keepalive_connections=concurrency)
    async with httpx.AsyncClient(limits=limits, http2=False) as client:
        with OUTPUT_FILE.open("a", encoding="utf-8") as out_f:
            tasks = [
                asyncio.create_task(translate_row(sem, client, row, idx, max_retries))
                for idx, row in pending
            ]
            for fut in atqdm.as_completed(tasks, total=len(tasks)):
                try:
                    result = await fut
                except Exception as e:
                    err_count += 1
                    print(f"\n[error] {e}", file=sys.stderr)
                    continue
                async with file_lock:
                    out_f.write(json.dumps(result, ensure_ascii=False) + "\n")
                    out_f.flush()

    print(f"Done. Errors: {err_count}", file=sys.stderr)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None, help="Translate only first N rows (for dry runs)")
    p.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    p.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES_SIMPLIFIED,
                   help="Max retries when simplified chars detected")
    args = p.parse_args()
    asyncio.run(run(args.limit, args.concurrency, args.max_retries))


if __name__ == "__main__":
    main()
