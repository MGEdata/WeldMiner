"""Streamlit frontend for SQL, process-vector, and JSON Agentic RAG."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from RAGbot import WeldingAgenticRAG
from RAGbot.config import DEFAULT_TOP_K, RAG_DATABASE_PATH


DATA_DIRECTORY = PROJECT_ROOT / "数据集可视化分析"
_configured_database = Path(RAG_DATABASE_PATH).expanduser()
DEFAULT_DATABASE = (
    _configured_database
    if _configured_database.is_absolute()
    else PROJECT_ROOT / _configured_database
)

EXAMPLE_QUESTIONS = (
    "Which X80 welded specimen has the highest HAZ impact energy, and what welding method and process parameters are associated with it?",
    "How does impact energy differ across heat inputs for comparable materials, welding methods, and testing regions?",
    "For the HAZ of X80 specimens welded by GMAW using WER70 filler metal, compare replicate impact energies, means, and standard deviations at -20°C and -40°C.",
)


st.set_page_config(
    page_title="WeldMiner Agentic RAG",
    page_icon="R",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --rag-ink: #17202a;
        --rag-muted: #5f6b76;
        --rag-line: #d9dee3;
        --rag-accent: #087f8c;
        --rag-warm: #b55b22;
    }
    .stApp { color: var(--rag-ink); }
    [data-testid="stSidebar"] { border-right: 1px solid var(--rag-line); }
    [data-testid="stMetric"] {
        border-top: 2px solid var(--rag-accent);
        padding-top: 0.55rem;
    }
    [data-testid="stChatMessage"] {
        border-bottom: 1px solid var(--rag-line);
        border-radius: 0;
        padding: 1rem 0;
    }
    .rag-kicker {
        color: var(--rag-accent);
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0;
        margin-bottom: 0.15rem;
    }
    .rag-subtitle { color: var(--rag-muted); margin-bottom: 1.2rem; }
    .rag-source { color: var(--rag-warm); font-weight: 650; }
    div[data-testid="stExpander"] { border-radius: 4px; }
    button[kind="secondary"] { border-radius: 4px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _database_options() -> List[Path]:
    databases = sorted(DATA_DIRECTORY.glob("*.db")) if DATA_DIRECTORY.exists() else []
    if DEFAULT_DATABASE in databases:
        databases.remove(DEFAULT_DATABASE)
        databases.insert(0, DEFAULT_DATABASE)
    return databases


@st.cache_resource(show_spinner=False)
def _build_rag(
    db_path: str,
    top_k: int,
    max_agent_iterations: int,
    process_candidate_limit: int,
) -> WeldingAgenticRAG:
    rag = WeldingAgenticRAG(
        db_path=db_path,
        top_k=top_k,
        max_agent_iterations=max_agent_iterations,
        process_candidate_limit=process_candidate_limit,
    )
    if not rag.index_database():
        raise RuntimeError("The database contains no usable specimen or paper records.")
    return rag


def _measurement_rows(specimens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for specimen in specimens:
        for prop in specimen.get("properties", []):
            rows.append(
                {
                    "Testing region": specimen.get("test_area") or "Not specified",
                    "Property": prop.get("property_name"),
                    "Property target": {
                        "specimen": "Specimen",
                        "base_metal": "Base metal reference",
                        "filler_metal": "Filler metal reference",
                    }.get(prop.get("property_target"), "Not specified"),
                    "Target index": prop.get("target_id"),
                    "Raw value": prop.get("raw_value"),
                    "Mean value": prop.get("average_value"),
                    "Unit": prop.get("property_unit"),
                }
            )
    return rows


def _process_parameter_rows(specimens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for specimen in specimens:
        for parameter in specimen.get("process_parameters", []):
            rows.append(
                {
                    "Specimen ID": specimen.get("specimen_id"),
                    "Process action": parameter.get("action_name") or "Unspecified",
                    "Original parameter name": parameter.get("parameter_name"),
                    "Raw value": parameter.get("raw_value"),
                    "Original unit": parameter.get("unit_raw"),
                    "Normalized value": parameter.get("canonical_value"),
                    "Normalized minimum": parameter.get("canonical_min"),
                    "Normalized maximum": parameter.get("canonical_max"),
                    "Normalized unit": parameter.get("canonical_unit"),
                    "JSON path": parameter.get("json_path"),
                }
            )
    return rows


def _render_evidence(hits: List[Dict[str, Any]]) -> None:
    if not hits:
        st.info("No retrieval evidence is available for this query.")
        return

    st.caption(f"Showing {len(hits)} retrieved evidence records in retrieval order.")
    for rank, hit in enumerate(hits, start=1):
        metadata = hit.get("metadata", {})
        evidence = metadata.get("evidence", {})
        specimens = evidence.get("specimens", [])
        source = evidence.get("paper") or "Source not specified"
        area = next(
            (item.get("test_area") for item in specimens if item.get("test_area")),
            "Region not specified",
        )
        title = f"{rank}. {evidence.get('base_metal') or 'Material not specified'} · {area} · {source}"

        with st.expander(title, expanded=rank == 1):
            left, middle, right = st.columns([1, 1, 1])
            left.markdown(f"**Welding method**  \n{evidence.get('welding_method') or 'Not specified'}")
            middle.markdown(f"**Filler metal**  \n{evidence.get('filler_metal') or 'Not specified'}")
            right.markdown(
                f"**Retrieval details**  \nScore {float(hit.get('score', 0)):.2f} · "
                f"{', '.join(hit.get('channels', [])) or 'unknown'}"
            )

            measurement_tab, process_tab, raw_tab = st.tabs(
                ["Measurements and test conditions", "Welding process parameters", "Original context"]
            )
            with measurement_tab:
                rows = _measurement_rows(specimens)
                if rows:
                    st.dataframe(rows, use_container_width=True, hide_index=True)

                for specimen in specimens:
                    details = []
                    if specimen.get("test_method"):
                        details.append(f"Test method: {specimen['test_method']}")
                    if specimen.get("test_condition"):
                        condition = specimen["test_condition"]
                        if isinstance(condition, dict):
                            condition = "; ".join(
                                f"{key}: {value}" for key, value in condition.items()
                            )
                        details.append(f"Test conditions: {condition}")
                    if details:
                        st.markdown("  \n".join(details))

            with process_tab:
                process_rows = _process_parameter_rows(specimens)
                if process_rows:
                    st.markdown("**Process parameters selected by the agent**")
                    st.dataframe(process_rows, use_container_width=True, hide_index=True)
                if evidence.get("welding_params"):
                    st.markdown("**Original welding_params JSON**")
                    st.json(evidence["welding_params"], expanded=False)
                else:
                    st.caption("This record has no welding_params JSON.")

            with raw_tab:
                st.code(hit.get("context", "")[:12000], language="text")

            st.markdown(f"<span class='rag-source'>Source: {source}</span>", unsafe_allow_html=True)


def _compact_hits(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    compact = []
    for hit in hits:
        item = dict(hit)
        item["context"] = item.get("context", "")[:12000]
        compact.append(item)
    return compact


def _render_query_plan(plan: Dict[str, Any] | None, planning_error: str | None) -> None:
    if plan:
        with st.expander("Agent retrieval plan"):
            st.caption(
                f"Target property: {plan.get('target_property') or 'None'} · "
                f"Property target: {plan.get('property_target', 'specimen')} · "
                f"Access mode: {plan.get('process_access_mode', 'none')} · "
                f"Task: {plan.get('process_task', 'none')}"
            )
            if plan.get("process_parameter_query"):
                st.markdown(f"**Process parameter concept**  \n{plan['process_parameter_query']}")
            if plan.get("comparison_controls"):
                st.markdown("**Comparison control fields**  \n" + ", ".join(plan["comparison_controls"]))
            if plan.get("sql"):
                st.code(plan["sql"], language="sql")
                st.markdown("**Query parameters**")
                st.json(plan.get("parameters", {}), expanded=False)
    if planning_error:
        st.warning(f"Agent retrieval planning failed: {planning_error}")


def _render_agent_trace(
    trace: List[Dict[str, Any]] | None,
    process_analysis: Dict[str, Any] | None,
) -> None:
    if trace:
        with st.expander("Agent iteration trace"):
            for item in trace:
                st.markdown(
                    f"**Iteration {item.get('iteration', 0)} · {item.get('tool', 'tool')} · "
                    f"{item.get('status', 'unknown')}**"
                )
                st.json(item.get("detail", {}), expanded=False)
    if process_analysis:
        with st.expander("Runtime process-property statistics"):
            warnings = process_analysis.get("warnings") or []
            for warning in warnings:
                st.warning(warning)
            st.json(process_analysis, expanded=False)


def _render_message(message: Dict[str, Any]) -> None:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("error"):
            st.warning(message["error"])
        _render_query_plan(message.get("query_plan"), message.get("planning_error"))
        _render_agent_trace(message.get("agent_trace"), message.get("process_analysis"))
        if message.get("contexts"):
            st.markdown("**Structured retrieval evidence**")
            _render_evidence(message["contexts"])


def _run_question(question: str) -> None:
    rag = st.session_state.rag
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Executing SQL and selecting a process JSON access strategy..."):
            result = rag.query(question, top_k=st.session_state.active_top_k)
        answer = result.get("answer") or "No answer was generated."
        st.markdown(answer)
        error = result.get("error")
        if error:
            st.warning(error)
        query_plan = result.get("query_plan")
        planning_error = result.get("planning_error")
        _render_query_plan(query_plan, planning_error)
        agent_trace = result.get("agent_trace", [])
        process_analysis = result.get("process_analysis")
        _render_agent_trace(agent_trace, process_analysis)
        contexts = _compact_hits(result.get("contexts", []))
        if contexts:
            st.markdown("**Structured retrieval evidence**")
            _render_evidence(contexts)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "error": error,
            "query_plan": query_plan,
            "planning_error": planning_error,
            "agent_trace": agent_trace,
            "process_analysis": process_analysis,
            "contexts": contexts,
        }
    )


for key, default in (
    ("rag", None),
    ("messages", []),
    ("active_database", ""),
    ("active_top_k", DEFAULT_TOP_K),
):
    if key not in st.session_state:
        st.session_state[key] = default


with st.sidebar:
    st.header("Retrieval settings")
    database_options = _database_options()
    if database_options:
        selected_database = st.selectbox(
            "Database",
            database_options,
            format_func=lambda path: path.name,
        )
        database_path = st.text_input("Database path", value=str(selected_database))
    else:
        database_path = st.text_input("Database path", value=str(DEFAULT_DATABASE))

    top_k = st.slider("Results to return", min_value=3, max_value=12, value=8, step=1)
    max_agent_iterations = st.slider("Maximum agent iterations", min_value=1, max_value=3, value=3)
    process_candidate_limit = st.slider(
        "Candidates for process comparison", min_value=30, max_value=200, value=120, step=10
    )

    if st.button("Load database", type="primary", use_container_width=True):
        try:
            with st.spinner("Loading relational records..."):
                st.session_state.rag = _build_rag(
                    database_path,
                    top_k,
                    max_agent_iterations,
                    process_candidate_limit,
                )
            st.session_state.active_database = database_path
            st.session_state.active_top_k = top_k
            st.session_state.messages = []
            st.success("Database loaded")
        except Exception as exc:
            st.session_state.rag = None
            st.error(str(exc))

    if st.session_state.rag:
        stats = st.session_state.rag.get_stats()
        st.divider()
        st.caption("Runtime status")
        st.write(f"Specimen records: {stats['record_count']}")
        st.write(f"Paper records: {stats['paper_count']}")
        st.write(f"Generation model: {stats['llm_model']}")
        st.write(f"SQL planning: {'Enabled' if stats['sql_planner_enabled'] else 'Disabled'}")
        st.write(f"Maximum agent iterations: {stats['max_agent_iterations']}")
        st.write(
            f"Process vectors: {'Available' if stats['process_vector_available'] else 'Unavailable'}"
        )
        st.write(f"Process embedding model: {stats['process_vector_model']}")
        st.write(f"Encoded action/parameter pairs: {stats['process_vector_index_count']}")
        st.write("Retrieval tools: " + ", ".join(stats["retrieval_tools"]))

    st.divider()
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


st.markdown('<div class="rag-kicker">Welding Intelligence</div>', unsafe_allow_html=True)
st.title("WeldMiner Agentic RAG")
st.markdown(
    '<div class="rag-subtitle">SQL filters relational records; complete processes are read directly, while specific parameters use vector retrieval and JSON verification.</div>',
    unsafe_allow_html=True,
)

if st.session_state.rag:
    stats = st.session_state.rag.get_stats()
    metric_columns = st.columns(4)
    metric_columns[0].metric("Specimen records", f"{stats['record_count']:,}")
    metric_columns[1].metric("Paper records", f"{stats['paper_count']:,}")
    metric_columns[2].metric("Results to return", st.session_state.active_top_k)
    metric_columns[3].metric("Generation model", stats["llm_model"])

    st.subheader("Example queries")
    quick_columns = st.columns(3)
    quick_question = None
    for column, question in zip(quick_columns, EXAMPLE_QUESTIONS):
        if column.button(question, use_container_width=True):
            quick_question = question

    st.divider()
    for message in st.session_state.messages:
        _render_message(message)

    submitted_question = st.chat_input("Ask about materials, processes, testing regions, properties, or thresholds")
    question = quick_question or submitted_question
    if question:
        _run_question(question)
else:
    st.info("Select and load a database in the sidebar.")
