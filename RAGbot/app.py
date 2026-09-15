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
    "在X80焊接试样中，HAZ冲击功最高的记录是什么？请反推焊接方法和工艺参数。",
    "在可比的材料、焊法和测试区域内，不同热输入下冲击功有什么数据差异？",
    "对X80、GMAW、WER70焊材的HAZ，比较-20°C和-40°C冲击功的平行试样值、平均值和标准差。",
)


st.set_page_config(
    page_title="焊接数据 Agentic RAG",
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
        raise RuntimeError("数据库中没有可索引的试样或论文记录。")
    return rag


def _measurement_rows(specimens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for specimen in specimens:
        for prop in specimen.get("properties", []):
            rows.append(
                {
                    "测试区域": specimen.get("test_area") or "未标注",
                    "性能": prop.get("property_name"),
                    "性能对象": {
                        "specimen": "当前试样",
                        "base_metal": "母材参考",
                        "filler_metal": "焊材参考",
                    }.get(prop.get("property_target"), "未标注"),
                    "对象序号": prop.get("target_id"),
                    "原始值": prop.get("raw_value"),
                    "平均值": prop.get("average_value"),
                    "单位": prop.get("property_unit"),
                }
            )
    return rows


def _process_parameter_rows(specimens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for specimen in specimens:
        for parameter in specimen.get("process_parameters", []):
            rows.append(
                {
                    "试样ID": specimen.get("specimen_id"),
                    "工艺动作": parameter.get("action_name") or "未限定",
                    "原始参数名": parameter.get("parameter_name"),
                    "原始值": parameter.get("raw_value"),
                    "原始单位": parameter.get("unit_raw"),
                    "规范值": parameter.get("canonical_value"),
                    "规范下限": parameter.get("canonical_min"),
                    "规范上限": parameter.get("canonical_max"),
                    "规范单位": parameter.get("canonical_unit"),
                    "JSON路径": parameter.get("json_path"),
                }
            )
    return rows


def _render_evidence(hits: List[Dict[str, Any]]) -> None:
    if not hits:
        st.info("本次查询没有检索证据。")
        return

    st.caption(f"共显示 {len(hits)} 条检索证据，按综合相关性排序。")
    for rank, hit in enumerate(hits, start=1):
        metadata = hit.get("metadata", {})
        evidence = metadata.get("evidence", {})
        specimens = evidence.get("specimens", [])
        source = evidence.get("paper") or "来源未标注"
        area = next(
            (item.get("test_area") for item in specimens if item.get("test_area")),
            "区域未标注",
        )
        title = f"{rank}. {evidence.get('base_metal') or '材料未标注'} · {area} · {source}"

        with st.expander(title, expanded=rank == 1):
            left, middle, right = st.columns([1, 1, 1])
            left.markdown(f"**焊接方法**  \n{evidence.get('welding_method') or '未标注'}")
            middle.markdown(f"**焊材**  \n{evidence.get('filler_metal') or '未标注'}")
            right.markdown(
                f"**检索信息**  \n得分 {float(hit.get('score', 0)):.2f} · "
                f"{', '.join(hit.get('channels', [])) or 'unknown'}"
            )

            measurement_tab, process_tab, raw_tab = st.tabs(
                ["测量与测试条件", "焊接工艺参数", "原始上下文"]
            )
            with measurement_tab:
                rows = _measurement_rows(specimens)
                if rows:
                    st.dataframe(rows, use_container_width=True, hide_index=True)

                for specimen in specimens:
                    details = []
                    if specimen.get("test_method"):
                        details.append(f"测试方法：{specimen['test_method']}")
                    if specimen.get("test_condition"):
                        condition = specimen["test_condition"]
                        if isinstance(condition, dict):
                            condition = "；".join(
                                f"{key}：{value}" for key, value in condition.items()
                            )
                        details.append(f"测试条件：{condition}")
                    if details:
                        st.markdown("  \n".join(details))

            with process_tab:
                process_rows = _process_parameter_rows(specimens)
                if process_rows:
                    st.markdown("**本轮 Agent 命中的工艺参数**")
                    st.dataframe(process_rows, use_container_width=True, hide_index=True)
                if evidence.get("welding_params"):
                    st.markdown("**原始 welding_params JSON**")
                    st.json(evidence["welding_params"], expanded=False)
                else:
                    st.caption("该记录没有 welding_params JSON。")

            with raw_tab:
                st.code(hit.get("context", "")[:12000], language="text")

            st.markdown(f"<span class='rag-source'>来源：{source}</span>", unsafe_allow_html=True)


def _compact_hits(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    compact = []
    for hit in hits:
        item = dict(hit)
        item["context"] = item.get("context", "")[:12000]
        compact.append(item)
    return compact


def _render_query_plan(plan: Dict[str, Any] | None, planning_error: str | None) -> None:
    if plan:
        with st.expander("Agent 检索计划"):
            st.caption(
                f"目标属性：{plan.get('target_property') or '无'} · "
                f"性能对象：{plan.get('property_target', 'specimen')} · "
                f"访问模式：{plan.get('process_access_mode', 'none')} · "
                f"任务：{plan.get('process_task', 'none')}"
            )
            if plan.get("process_parameter_query"):
                st.markdown(f"**工艺参数概念**  \n{plan['process_parameter_query']}")
            if plan.get("comparison_controls"):
                st.markdown("**比较控制字段**  \n" + "、".join(plan["comparison_controls"]))
            if plan.get("sql"):
                st.code(plan["sql"], language="sql")
                st.markdown("**查询参数**")
                st.json(plan.get("parameters", {}), expanded=False)
    if planning_error:
        st.warning(f"Agent 检索规划失败：{planning_error}")


def _render_agent_trace(
    trace: List[Dict[str, Any]] | None,
    process_analysis: Dict[str, Any] | None,
) -> None:
    if trace:
        with st.expander("Agent 循环记录"):
            for item in trace:
                st.markdown(
                    f"**第 {item.get('iteration', 0)} 轮 · {item.get('tool', 'tool')} · "
                    f"{item.get('status', 'unknown')}**"
                )
                st.json(item.get("detail", {}), expanded=False)
    if process_analysis:
        with st.expander("运行时工艺-性能统计"):
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
            st.markdown("**结构化检索证据**")
            _render_evidence(message["contexts"])


def _run_question(question: str) -> None:
    rag = st.session_state.rag
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("正在执行SQL并选择工艺JSON访问路径..."):
            result = rag.query(question, top_k=st.session_state.active_top_k)
        answer = result.get("answer") or "未生成回答。"
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
            st.markdown("**结构化检索证据**")
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
    st.header("检索配置")
    database_options = _database_options()
    if database_options:
        selected_database = st.selectbox(
            "数据库",
            database_options,
            format_func=lambda path: path.name,
        )
        database_path = st.text_input("数据库路径", value=str(selected_database))
    else:
        database_path = st.text_input("数据库路径", value=str(DEFAULT_DATABASE))

    top_k = st.slider("召回数量", min_value=3, max_value=12, value=8, step=1)
    max_agent_iterations = st.slider("Agent 最大循环", min_value=1, max_value=3, value=3)
    process_candidate_limit = st.slider(
        "工艺比较候选数", min_value=30, max_value=200, value=120, step=10
    )

    if st.button("加载数据库", type="primary", use_container_width=True):
        try:
            with st.spinner("正在加载关系记录..."):
                st.session_state.rag = _build_rag(
                    database_path,
                    top_k,
                    max_agent_iterations,
                    process_candidate_limit,
                )
            st.session_state.active_database = database_path
            st.session_state.active_top_k = top_k
            st.session_state.messages = []
            st.success("数据库已加载")
        except Exception as exc:
            st.session_state.rag = None
            st.error(str(exc))

    if st.session_state.rag:
        stats = st.session_state.rag.get_stats()
        st.divider()
        st.caption("运行状态")
        st.write(f"试样记录：{stats['record_count']}")
        st.write(f"论文记录：{stats['paper_count']}")
        st.write(f"生成模型：{stats['llm_model']}")
        st.write(f"SQL 规划：{'开启' if stats['sql_planner_enabled'] else '关闭'}")
        st.write(f"Agent 循环上限：{stats['max_agent_iterations']}")
        st.write(
            f"工艺向量：{'可用' if stats['process_vector_available'] else '不可用'}"
        )
        st.write(f"工艺Embedding：{stats['process_vector_model']}")
        st.write(f"已编码动作-参数对：{stats['process_vector_index_count']}")
        st.write("检索工具：" + "、".join(stats["retrieval_tools"]))

    st.divider()
    if st.button("清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


st.markdown('<div class="rag-kicker">Welding Intelligence</div>', unsafe_allow_html=True)
st.title("焊接数据 Agentic RAG")
st.markdown(
    '<div class="rag-subtitle">SQL筛选关系数据，完整工艺直接读取，特定参数使用向量召回与JSON验证。</div>',
    unsafe_allow_html=True,
)

if st.session_state.rag:
    stats = st.session_state.rag.get_stats()
    metric_columns = st.columns(4)
    metric_columns[0].metric("试样记录", f"{stats['record_count']:,}")
    metric_columns[1].metric("论文记录", f"{stats['paper_count']:,}")
    metric_columns[2].metric("召回数量", st.session_state.active_top_k)
    metric_columns[3].metric("生成模型", stats["llm_model"])

    st.subheader("快速查询")
    quick_columns = st.columns(3)
    quick_question = None
    for column, question in zip(quick_columns, EXAMPLE_QUESTIONS):
        if column.button(question, use_container_width=True):
            quick_question = question

    st.divider()
    for message in st.session_state.messages:
        _render_message(message)

    submitted_question = st.chat_input("输入材料、工艺、测试区域、性能或阈值条件")
    question = quick_question or submitted_question
    if question:
        _run_question(question)
else:
    st.info("请在左侧选择数据库并加载。")
