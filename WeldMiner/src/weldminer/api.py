"""Public parsing and single-file extraction interfaces.

Calls are serialized because the inherited workflow uses a module-level output path.
"""
from pathlib import Path
import hashlib
import json
from threading import RLock
from time import perf_counter
from .config import ExtractionConfig
from .readers.parsing import parse_pdf, parse_xml

__all__ = ['parse_pdf', 'parse_xml', 'extract_file']

_LOCK = RLock()
SUPPORTED_EXTENSIONS = {'.xml', '.md', '.markdown', '.txt'}

def extract_file(path: str | Path, config: ExtractionConfig | None = None, *,
                 output_dir: str | Path = 'output', overwrite: bool = False,
                 node_llms: dict | None = None) -> dict:
    """Return status, output location, elapsed seconds and JSON-compatible workflow state.

    Inject node_llms to reuse configured LangChain clients. Errors raise exceptions.
    PDF must be converted with parse_pdf before extraction.
    """
    config = config or ExtractionConfig()
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f'Unsupported extraction input: {source.suffix}; convert PDF with parse_pdf first')
    digest = hashlib.sha256(str(source).encode()).hexdigest()[:12]
    folder = Path(output_dir).expanduser().resolve() / f'{source.stem}-{digest}'
    signature = hashlib.sha256(source.read_bytes() + config.model_dump_json().encode()).hexdigest()
    marker = folder / 'run.json'
    with _LOCK:
        if marker.exists() and not overwrite:
            previous = json.loads(marker.read_text(encoding='utf-8'))
            if previous.get('signature') == signature and previous.get('status') == 'success' and (folder / 'result.json').exists():
                return {**previous, 'status': 'skipped', 'result': json.loads((folder / 'result.json').read_text(encoding='utf-8'))}
            raise FileExistsError(f'Existing output differs or is incomplete: {folder}; use overwrite=True')
        if folder.exists() and not overwrite:
            raise FileExistsError(f'Incomplete output exists: {folder}; use overwrite=True')
        from .readers.parser import load_document_input
        from .models.data_schemas import ExtractionWorkflowState
        from .extraction.workflow import create_layered_workflow
        from .llm.providers import create_node_llms
        from .exporters.results import save_result, write_json
        started = perf_counter()
        loaded = load_document_input(source)
        if loaded is None:
            raise ValueError(f'Parser produced no usable content: {source}')
        document_id, raw = loaded
        workflow = create_layered_workflow(
            node_llms=node_llms if node_llms is not None else create_node_llms(config),
            json_output_dir=str(folder))
        state = workflow.invoke(ExtractionWorkflowState(raw_text=raw,
            **{key: getattr(config, key) for key in ('material_user_goal', 'material_direct_goal',
                                                   'sample_user_goal', 'sample_direct_goal')}))
        if isinstance(state, dict):
            state = ExtractionWorkflowState(**state)
        save_result(state, folder, config)
        status = 'failed' if state.error_message else ('success' if state.final_result else 'empty')
        record = {'source': str(source), 'document_id': document_id, 'output_dir': str(folder),
                  'status': status, 'error': state.error_message, 'signature': signature,
                  'seconds': round(perf_counter() - started, 3)}
        write_json(marker, record)
        return {**record, 'result': state.model_dump(mode='json')}
