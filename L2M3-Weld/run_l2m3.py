"""Runner for L2M3-Weld experiments."""
import copy
import csv
import hashlib
import json
import os
import random
import time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field

# Edit this section, then run this file directly in your IDE.
INPUT_PATH = ""  # One XML file or a folder (searched recursively).
OUTPUT_DIR = "outputs"
ENV_FILE = ".env"
API_KEY = ""  # Optional; otherwise read DASHSCOPE_API_KEY / QWEN_API_KEY.
BASE_URL = ""  # Optional; otherwise use .env or the DashScope compatible endpoint.
MODEL = "qwen3.7-max"
PUBLISHER = "elsevier"  # elsevier, acs, rsc, springer
TEMPERATURE = 0.0
MAX_TOKENS = 8192
THINKING = False
RETRIES = 2
TIMEOUT = 180
LIMIT = 0  # 0 = all XML files.
OVERWRITE = False


def make_config():
    load_dotenv(ENV_FILE, override=False)
    return SimpleNamespace(
        input=Path(INPUT_PATH), output=Path(OUTPUT_DIR), model=MODEL,
        api_key=API_KEY or os.getenv('DASHSCOPE_API_KEY') or os.getenv('QWEN_API_KEY'),
        base_url=BASE_URL or os.getenv('DASHSCOPE_BASE_URL') or os.getenv('QWEN_API_BASE_URL')
                 or 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        publisher=PUBLISHER, temperature=TEMPERATURE, max_tokens=MAX_TOKENS,
        thinking=THINKING, retries=RETRIES, timeout=TIMEOUT, limit=LIMIT,
        overwrite=OVERWRITE,
    )


class Meter:
    def __init__(self):
        self.events = []
        self.log_path = None

    def reset(self, log_path):
        self.events = []
        self.log_path = Path(log_path)
        self.log_path.write_text('', encoding='utf-8')

    def record(self, event):
        self.events.append(event)
        if self.log_path:
            with self.log_path.open('a', encoding='utf-8') as handle:
                handle.write(json.dumps(event, ensure_ascii=False) + '\n')

    def summary(self):
        usages = [e['usage'] for e in self.events if e.get('usage')]
        return {
            'api_attempts': len(self.events),
            'api_errors': sum(e.get('error') is not None for e in self.events),
            'usage_complete': all(e.get('usage') is not None for e in self.events),
            'input_tokens': sum(u.get('prompt_tokens', 0) for u in usages),
            'output_tokens': sum(u.get('completion_tokens', 0) for u in usages),
            'total_tokens': sum(u.get('total_tokens', 0) for u in usages),
            'reasoning_tokens': sum((u.get('completion_tokens_details') or {}).get('reasoning_tokens', 0) for u in usages),
            'cached_input_tokens': sum((u.get('prompt_tokens_details') or {}).get('cached_tokens', 0) for u in usages),
            'api_seconds': round(sum(e['seconds'] for e in self.events), 3),
        }


class QwenChat(BaseChatModel):
    model_name: str = 'qwen3.7-max'
    client: Any = Field(exclude=True)
    meter: Any = Field(exclude=True)
    temperature: float = 0.0
    max_tokens: int = 8192
    retries: int = 2
    thinking: bool = False

    @property
    def _llm_type(self):
        return 'qwen-openai-compatible'

    @property
    def _identifying_params(self):
        return {'model_name': self.model_name, 'temperature': self.temperature}

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        role_map = {'human': 'user', 'ai': 'assistant', 'system': 'system'}
        payload = [{'role': role_map[m.type], 'content': m.content} for m in messages]
        # Include reasoning in the configured output budget when enabled.
        budget = self.max_tokens if self.thinking else kwargs.get('max_tokens', self.max_tokens)
        for attempt in range(self.retries + 1):
            started = time.perf_counter()
            event = {'attempt': attempt + 1, 'model': self.model_name, 'max_tokens': budget,
                     'usage': None, 'error': None}
            response = None
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name, messages=payload, temperature=self.temperature,
                    max_tokens=budget, stop=stop, extra_body={'enable_thinking': self.thinking},
                )
                event['usage'] = response.usage.model_dump() if response.usage else None
                event['response_id'] = response.id
                choice = response.choices[0]
                event['finish_reason'] = choice.finish_reason
                if choice.finish_reason == 'length':
                    raise RuntimeError('Qwen output truncated; increase MAX_TOKENS (or set THINKING = False).')
                content = choice.message.content or ''
                if not content.strip():
                    raise RuntimeError('Qwen returned no final answer.')
            except Exception as exc:
                event['error'] = str(exc)
                event['seconds'] = time.perf_counter() - started
                self.meter.record(event)
                code = getattr(exc, 'status_code', None)
                retryable = response is None and (code is None or code in (408, 409, 429) or code >= 500)
                if not retryable or attempt == self.retries:
                    raise
                time.sleep(min(2 ** attempt, 8))
                continue
            event['seconds'] = time.perf_counter() - started
            self.meter.record(event)
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))],
                              llm_output={'token_usage': event['usage'] or {}, 'model_name': self.model_name})


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def build_processor(args, llm):
    from llm_miner.reader import JournalReader
    from llm_miner.agent import LLMMiner
    agent = LLMMiner.from_llm(llm, llm)
    def process(file, folder):
        journal = JournalReader.from_file(str(file), args.publisher)
        if not journal.elements: raise ValueError('Original L2M3 parser found no elements; check PUBLISHER')
        write_json(folder / 'parsed.json', journal.to_dict())
        random.seed(0)  # Original table example selection is otherwise random.
        try:
            agent.invoke({'paragraph': journal, 'token_checker': None})
        finally:
            data = journal.to_dict()
            write_json(folder / 'result.json', data)
            clean = copy.deepcopy(data.get('result', {}))
            for record in clean.get('results', []):
                record.pop('origin_data', None)
                record.get('material', {}).pop('chemical_formula', None)
            write_json(folder / 'result_clean.json', clean)
        elements = journal.cln_elements if journal.cln_elements else journal.elements
        errors = [e.intermediate_step['batch_error'] for e in list(journal.elements) + list(elements)
                  if 'batch_error' in e.intermediate_step]
        return {'doi': journal.doi, 'records': len(journal.result), 'status': 'partial' if errors else 'success', 'error': '; '.join(errors) or None}
    return process


def run_batch(args=None):
    if args is None:
        args = make_config()
    if args.retries < 0 or args.max_tokens <= 0 or args.limit < 0:
        raise ValueError('RETRIES/LIMIT must be nonnegative and MAX_TOKENS must be positive')
    if args.publisher not in {'elsevier', 'acs', 'rsc', 'springer'}:
        raise ValueError('Unsupported PUBLISHER')
    root = args.input.resolve()
    files = sorted(p for p in root.rglob('*') if p.is_file() and p.suffix.lower() == '.xml') if root.is_dir() else ([root] if root.is_file() and root.suffix.lower() == '.xml' else [])
    if args.limit: files = files[:args.limit]
    if not files: raise ValueError(f'No XML files found: {root}; set INPUT_PATH.')
    meter = Meter()
    from openai import OpenAI
    key = args.api_key
    if not key: raise ValueError('Set API_KEY or DASHSCOPE_API_KEY / QWEN_API_KEY in .env')
    llm = QwenChat(client=OpenAI(api_key=key, base_url=args.base_url, timeout=args.timeout, max_retries=0),
                   meter=meter, model_name=args.model, temperature=args.temperature,
                   max_tokens=args.max_tokens, retries=args.retries, thinking=args.thinking)
    process = build_processor(args, llm)
    run_id = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    output = args.output.resolve() / 'l2m3'
    output.mkdir(parents=True, exist_ok=True)
    summaries = []
    batch_started = time.perf_counter()
    parent = root if root.is_dir() else root.parent
    for index, file in enumerate(files, 1):
        relative = file.relative_to(parent).as_posix()
        doc_key = file.stem[:70] + '-' + hashlib.sha256(relative.encode()).hexdigest()[:10]
        folder = output / doc_key
        folder.mkdir(exist_ok=True)
        marker = folder / 'stats.json'
        if marker.exists() and not args.overwrite:
            previous = json.loads(marker.read_text(encoding='utf-8'))
            if previous.get('status') == 'success':
                summaries.append({'file': relative, 'status': 'skipped', 'wall_seconds': 0})
                print(f'[{index}/{len(files)}] skipped {relative}', flush=True)
                continue
        # Keep old/failed attempts and their usage when rerunning a document.
        attempt_dir = folder / run_id
        attempt_dir.mkdir()
        meter.reset(attempt_dir / 'calls.jsonl')
        started = time.perf_counter()
        row = {'file': relative, 'status': 'success', 'error': None, 'run_id': run_id, 'output': str(attempt_dir)}
        try:
            row.update(process(file, attempt_dir))
        except Exception as exc:
            row.update(status='failed', error=str(exc))
        row.update(meter.summary())
        row['wall_seconds'] = round(time.perf_counter() - started, 3)
        write_json(attempt_dir / 'stats.json', row)
        write_json(marker, row)
        summaries.append(row)
        print(f'[{index}/{len(files)}] {relative}: {row["status"]}, {row["total_tokens"]} tokens, {row["wall_seconds"]} s', flush=True)
        save_summary(output, run_id, summaries, args, batch_started)
    save_summary(output, run_id, summaries, args, batch_started)
    return 1 if any(r['status'] != 'success' and r['status'] != 'skipped' for r in summaries) else 0


def save_summary(output, run_id, rows, args, started):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with (output / f'summary-{run_id}.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    counts = {k: sum(r.get(k, 0) for r in rows) for k in ['input_tokens', 'output_tokens', 'total_tokens', 'reasoning_tokens', 'cached_input_tokens', 'api_attempts', 'api_errors', 'api_seconds']}
    write_json(output / f'summary-{run_id}.json', {
        'run_id': run_id, 'model': args.model, 'base_url': args.base_url,
        'thinking': args.thinking, 'temperature': args.temperature,
        'max_tokens': args.max_tokens, 'publisher': args.publisher,
        'wall_seconds': round(time.perf_counter() - started, 3), **counts,
        'usage_complete': all(r.get('usage_complete', True) for r in rows), 'documents': rows,
    })


if __name__ == '__main__':
    raise SystemExit(run_batch())
