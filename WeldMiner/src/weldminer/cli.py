"""Command-line frontend; imports do not start extraction or configure credentials."""
import argparse
import json
from pathlib import Path
from .api import extract_file, parse_pdf, parse_xml
from .config import ExtractionConfig

def main(argv=None):
    parser = argparse.ArgumentParser(description='Parse or extract one document')
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=Path('output'))
    parser.add_argument('--config', type=Path, help='JSON extraction/model configuration')
    parser.add_argument('--env-file', type=Path, help='Explicit dotenv file; existing environment wins')
    parser.add_argument('--overwrite', action='store_true')
    parser.add_argument('--action', choices=['parse', 'extract'], default='extract')
    args = parser.parse_args(argv)
    try:
        if args.env_file:
            if not args.env_file.is_file():
                raise FileNotFoundError(args.env_file)
            from dotenv import load_dotenv
            load_dotenv(args.env_file, override=False)
        if not args.input.is_file():
            raise ValueError('Input must be a single file; use a Python loop for multiple files')
        if args.action == 'parse':
            if args.input.suffix.lower() == '.pdf':
                print(parse_pdf(args.input))
            elif args.input.suffix.lower() == '.xml':
                print(parse_xml(args.input))
            else:
                raise ValueError('Parsing supports only PDF or XML')
            return 0
        config = ExtractionConfig.from_file(args.config) if args.config else ExtractionConfig()
        records = [extract_file(args.input, config, output_dir=args.output, overwrite=args.overwrite)]
        print(json.dumps([{k: v for k, v in r.items() if k != 'result'} for r in records], ensure_ascii=False, indent=2))
        return int(any(r['status'] in ('failed', 'empty') for r in records))
    except Exception as exc:
        parser.exit(1, f'Error: {exc}\n')

