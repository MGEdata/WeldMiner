"""Extract welding data from XML, Markdown or text; optionally parse XML first."""
import os
import sys
from pathlib import Path
from time import perf_counter

import weldminer
from dotenv import load_dotenv
from weldminer import ExtractionConfig, ModelConfig, parse_xml, extract_file


INPUT_FILE = ''
ENV_FILE = '.env'
OUTPUT_DIR = 'output'
OVERWRITE = False
MODE = 'extract'  # 'parse': 只解析；'extract': 只抽取；'both': 解析后抽取
API_KEY = ''  # 可以直接填写密钥字符串；None 表示从 .env 的 QWEN_API_KEY 读取

CONFIG = ExtractionConfig(
    material_user_goal=['hardness', 'tensile strength', 'yield strength', 'elongation'],
    material_direct_goal=[],
    sample_user_goal=['hardness', 'tensile strength', 'yield strength', 'elongation',
                      'Charpy impact test temperature', 'impact energy'],
    sample_direct_goal=[],  # For example: ['microstructure']
    llm=ModelConfig(provider='qwen', model='qwen3.7-max', api_key=API_KEY,
                    enable_reasoning=True),
    export_csv=True,
    export_excel=True,
)


def main():
    if MODE not in ('parse', 'extract', 'both'):
        raise ValueError("MODE must be 'parse', 'extract' or 'both'")
    print(f'Python: {sys.executable}')
    print(f'WeldMiner: {weldminer.__file__}')
    if Path(ENV_FILE).is_file():
        load_dotenv(ENV_FILE, override=False)
    source = Path(INPUT_FILE).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    extraction_input = source
    if MODE in ('parse', 'both'):
        parse_started = perf_counter()
        print(f'[1/2] 解析文件：{source}', flush=True)
        if source.suffix.lower() != '.xml':
            raise ValueError("Parsing requires XML; set MODE = 'extract' for Markdown/text")
        extraction_input = parse_xml(source)
        content = extraction_input.read_text(encoding='utf-8')
        print(f'Markdown: {extraction_input}\nCharacters: {len(content)}')
        print(f'解析耗时：{perf_counter() - parse_started:.1f} 秒')
        print(f'Preview:\n{content[:400]}')

    if MODE in ('extract', 'both'):
        if not CONFIG.llm.api_key and not os.getenv('QWEN_API_KEY'):
            raise ValueError(f'QWEN_API_KEY is missing; check {ENV_FILE}')
        print(f'[2/2] 使用 {CONFIG.llm.model} 抽取：{extraction_input}', flush=True)
        extract_started = perf_counter()
        record = extract_file(extraction_input, config=CONFIG, output_dir=OUTPUT_DIR,
                              overwrite=OVERWRITE)
        print(f"Status: {record['status']}\nOutput: {record['output_dir']}")
        print(f'抽取耗时：{perf_counter() - extract_started:.1f} 秒')
        state = record['result']
        print(f"Specimens: {len(state.get('skeleton') or [])}; final records: {len(state.get('final_result') or [])}")
        if record.get('error'):
            print(f"Error: {record['error']}")
        return 1 if record['status'] in ('failed', 'empty') else 0
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
