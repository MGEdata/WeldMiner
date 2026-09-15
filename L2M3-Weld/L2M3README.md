# L2M3-Weld experimental baseline

This directory contains welding-domain comparison code, not an installable Python package. `llm_miner/` comes from the adapted L2M3-master implementation and retains its parsing, stop sequences, extraction, and material-matching mechanisms. Prompts are adapted to welding; this is not the original MOF prompt version. The upstream license is retained in `LICENSE`.

## Installation and configuration

Create a dedicated Python environment and run these commands in this directory:

```powershell
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `QWEN_API_KEY` in `.env`. The runner reads this directory's `.env`, with existing environment variables taking precedence. Alternatively, set `API_KEY`, `BASE_URL`, and `ENV_FILE` at the top of the script. Do not commit real credentials.

## Run an experiment

Open `batch_l2m3.py` and edit its configuration:

```python
INPUT_PATH = PROJECT_DIR / "input"  # A single XML file or a directory
OUTPUT_DIR = PROJECT_DIR / "outputs"
MODEL = "qwen3.7-max"
PUBLISHER = "elsevier"
DRY_RUN = False
LIMIT = 0
OVERWRITE = False
```

Run the file directly in your IDE; no command-line arguments are required. Directories are searched recursively for XML files. `LIMIT = 0` processes all files. To check parsing without API calls, set `DRY_RUN = True` and `LIMIT = 1`; model-based table conversion and extraction are skipped. Set `DRY_RUN = False` for extraction.

Defaults are `MAX_TOKENS = 8192`, `THINKING = False`, and `TEMPERATURE = 0`. Use a model available to your API account. Supported publisher settings are `elsevier`, `acs`, `rsc`, and `springer`.

Existing successful results are skipped. Use a new output directory or `OVERWRITE = True` after changing models, prompts, inputs, or parameters: the runner does not compare old results against the new configuration. Papers with `partial` or `failed` status are processed again on the next run. Every attempt is stored separately without deleting older results.

## Outputs and accounting

Each paper has its own directory under `outputs/l2m3/`, with a separate subdirectory for each attempt:

| File | Contents |
| --- | --- |
| `parsed.json` | Original parser output |
| `result.json` | Complete extraction state, provenance, and matching results |
| `result_clean.json` | The result layer without per-record `origin_data` and `chemical_formula` |
| `calls.jsonl` | API usage, duration, finish reason, or error per attempt; no full prompts or answers |
| `stats.json` | Per-paper status, input/output/total tokens, and elapsed time |

Batch `summary-*.csv/json` files summarize actual usage and time. Token counts come from API usage and include input and output. Reasoning and cached tokens are subcategories and must not be added again. Requests without usage set `usage_complete=false`; estimated tokens are not substituted for provider usage. The script counts tokens, not monetary cost. `wall_seconds` is elapsed time; `api_seconds` sums API request durations.

A `success` status means no extraction error was captured; it does not guarantee completeness or correct material associations. Parse-only runs do not create extraction results.

## Code organization

- `batch_l2m3.py`: hardcoded settings, XML traversal, document extraction, Qwen API adapter, retries, accounting, and exports.
- `llm_miner/`: extraction core and welding prompts, independent of the external cross_evaluation directory.

Property targets are controlled by the prompts and `format/` templates. Historical defaults remain in `llm_miner/config.py`, but this runner creates and injects its client using `MODEL`.

Offline tests, when included in a development checkout, can be run with `python -m unittest discover -s tests -v`. Tests and `DRY_RUN` do not verify live Qwen connectivity or extraction accuracy.
