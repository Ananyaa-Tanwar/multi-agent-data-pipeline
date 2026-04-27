from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.io as pio
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.core.artifacts import init_state
from src.graph.pipeline_graph import build_graph

pio.templates.default = "plotly_white"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Multi-Agent Data Analyst",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: #1c1c1c; }
.stApp { background: #f8f7f4; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2.5rem 3.5rem 5rem 3.5rem; max-width: 1320px; }

/* ── Hero ── */
.hero-section { padding: 2.5rem 0 1.8rem 0; border-bottom: 1px solid #e8e5df; margin-bottom: 2rem; }
.hero-eyebrow { font-family:'DM Mono',monospace; font-size:0.7rem; font-weight:500; color:#888888; letter-spacing:0.14em; text-transform:uppercase; margin-bottom:0.6rem; }
.hero-title { font-family:'DM Serif Display',serif; font-size:2.8rem; font-weight:400; color:#1c1c1c; letter-spacing:-0.02em; line-height:1.15; margin:0 0 0.6rem 0; }
.hero-title em { font-style:italic; color:#3d3d3d; }
.hero-desc { font-size:0.92rem; color:#555555; line-height:1.65; max-width:620px; margin-bottom:1.6rem; }
.hero-desc strong { color:#1c1c1c; font-weight:600; }

/* ── Value props ── */
.value-props { display:grid; grid-template-columns:repeat(3,1fr); gap:0.75rem; margin-bottom:1.5rem; }
.value-prop { background:#ffffff; border:1px solid #e8e5df; border-radius:6px; padding:0.85rem 1rem; }
.value-prop-label { font-family:'DM Mono',monospace; font-size:0.62rem; color:#888888; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.25rem; }
.value-prop-text { font-size:0.82rem; color:#1c1c1c; font-weight:500; line-height:1.4; }

/* ── Pipeline steps ── */
.pipeline-row { display:flex; align-items:center; gap:0; flex-wrap:wrap; row-gap:0.3rem; margin-top:0.4rem; }
.pipeline-step { font-family:'DM Mono',monospace; font-size:0.72rem; font-weight:500; color:#3d3d3d; letter-spacing:0.02em; }
.pipeline-arrow { font-size:0.75rem; color:#aaaaaa; margin:0 0.45rem; line-height:1; }

/* ── Upload ── */
.upload-label { font-family:'DM Sans',sans-serif; font-size:0.9rem; font-weight:500; color:#3d3d3d; margin-bottom:0.6rem; }
[data-testid="stFileUploader"] { background:#ffffff!important; border:1.5px dashed #cccccc!important; border-radius:6px!important; transition:border-color 0.2s!important; }
[data-testid="stFileUploader"]:hover { border-color:#3d3d3d!important; }
.files-ready { font-family:'DM Mono',monospace; font-size:0.72rem; color:#3d7a3d; background:#f0f7f0; border:1px solid #c4dcc4; border-radius:4px; padding:0.4rem 0.8rem; margin:0.6rem 0; display:inline-block; }

/* ── Run button ── */
[data-testid="stButton"]>button { background:#1c1c1c!important; color:#f8f7f4!important; border:none!important; border-radius:6px!important; padding:0.6rem 2rem!important; font-family:'DM Sans',sans-serif!important; font-weight:600!important; font-size:0.88rem!important; letter-spacing:0.02em!important; transition:all 0.15s ease!important; }
[data-testid="stButton"]>button:hover { background:#333333!important; transform:translateY(-1px)!important; }

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] { background:transparent; border-bottom:1.5px solid #e8e5df; border-radius:0; padding:0; gap:0; }
[data-testid="stTabs"] button[role="tab"] { font-family:'DM Sans',sans-serif!important; font-size:0.82rem!important; font-weight:500!important; color:#888888!important; border-radius:0!important; padding:0.65rem 1.2rem!important; border:none!important; border-bottom:2px solid transparent!important; background:transparent!important; transition:all 0.15s!important; margin-bottom:-1.5px!important; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color:#1c1c1c!important; border-bottom:2px solid #3d3d3d!important; font-weight:600!important; background:transparent!important; }
[data-testid="stTabs"] button[role="tab"]:hover { color:#4a4a4a!important; background:transparent!important; }

/* ── Tab header ── */
.tab-title { font-family:'DM Serif Display',serif; font-size:1.5rem; font-weight:400; color:#1c1c1c; margin:1.5rem 0 0.3rem 0; letter-spacing:-0.01em; }
.tab-desc { font-size:0.82rem; color:#666666; line-height:1.6; margin-bottom:1.8rem; max-width:680px; }

/* ── Section headers ── */
.section-header { font-family:'DM Mono',monospace; font-size:0.68rem; font-weight:500; color:#888888; text-transform:uppercase; letter-spacing:0.12em; margin:2rem 0 0.8rem 0; padding-bottom:0.5rem; border-bottom:1px solid #e8e5df; }

/* ── Metric cards ── */
.metric-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:0.75rem; margin-bottom:2rem; }
.metric-card { background:#ffffff; border:1px solid #e8e5df; border-radius:6px; padding:1rem 1.1rem; }
.metric-label { font-family:'DM Mono',monospace; font-size:0.62rem; color:#888888; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.35rem; }
.metric-value { font-family:'DM Serif Display',serif; font-size:1.9rem; color:#1c1c1c; line-height:1; }
.metric-value.green { color:#3d7a3d; }
.metric-value.red { color:#a03030; }
.metric-value.muted { color:#888888; }

/* ── File cards ── */
.file-card { background:#ffffff; border:1px solid #e8e5df; border-radius:6px; padding:1rem 1.2rem; margin-bottom:0.6rem; }
.file-card-name { font-weight:600; font-size:0.9rem; color:#1c1c1c; margin-bottom:0.2rem; }
.file-card-meta { font-family:'DM Mono',monospace; font-size:0.68rem; color:#3d3d3d; margin-bottom:0.5rem; }
.col-chip { display:inline-block; background:#f2f2f2; border-radius:3px; padding:1px 6px; margin:2px; font-family:'DM Mono',monospace; font-size:0.63rem; color:#3d3d3d; }

/* ── Insight rows ── */
.insight-row { display:flex; align-items:baseline; gap:0.7rem; padding:0.6rem 0; border-bottom:1px solid #f0ede8; font-size:0.84rem; color:#2a2a2a; line-height:1.5; }
.insight-row:last-child { border-bottom:none; }
.insight-dot { width:4px; height:4px; border-radius:50%; background:#3d3d3d; flex-shrink:0; margin-top:0.5rem; }

/* ── AI insights ── */
.ai-label { font-family:'DM Mono',monospace; font-size:0.66rem; color:#888888; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:0.8rem; }
.ai-summary { background:#ffffff; border:1px solid #e8e5df; border-left:3px solid #3d3d3d; border-radius:0 6px 6px 0; padding:1.1rem 1.4rem; font-size:0.87rem; line-height:1.75; color:#2a2a2a; margin-bottom:1.2rem; }
.ai-section-title { font-family:'DM Mono',monospace; font-size:0.66rem; font-weight:500; color:#888888; text-transform:uppercase; letter-spacing:0.12em; margin:1.4rem 0 0.6rem 0; padding-bottom:0.4rem; border-bottom:1px solid #e8e5df; }
.ai-bullets { background:#ffffff; border:1px solid #e8e5df; border-radius:6px; padding:0.3rem 1rem; margin-bottom:0.4rem; }
.ai-bullet { display:flex; align-items:baseline; gap:0.65rem; padding:0.55rem 0; border-bottom:1px solid #f5f3f0; font-size:0.83rem; color:#2a2a2a; line-height:1.5; }
.ai-bullet:last-child { border-bottom:none; }
.ai-bullet-dot { width:4px; height:4px; border-radius:50%; background:#3d3d3d; flex-shrink:0; margin-top:0.48rem; }
.ai-rec-dot { width:4px; height:4px; border-radius:50%; background:#888888; flex-shrink:0; margin-top:0.48rem; }
.ai-warn-dot { width:4px; height:4px; border-radius:2px; background:#a07050; flex-shrink:0; margin-top:0.5rem; }

/* ── Chart builder callout ── */
.chart-builder-callout { background:#ffffff; border:1px solid #e8e5df; border-radius:6px; padding:0.9rem 1.1rem; margin-bottom:1.2rem; display:flex; align-items:center; gap:0.8rem; }
.chart-builder-callout-text { font-size:0.84rem; color:#3d3d3d; }
.chart-builder-callout-text strong { color:#1c1c1c; }

/* ── Ask anything ── */
.ask-input-wrap { margin-bottom: 0.6rem; }
.ask-result-answer {
    background: #ffffff;
    border: 1px solid #e8e5df;
    border-left: 3px solid #3d3d3d;
    border-radius: 0 6px 6px 0;
    padding: 1rem 1.3rem;
    font-size: 0.86rem;
    line-height: 1.75;
    color: #2a2a2a;
    margin-bottom: 1rem;
}
.ask-example {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    color: #888888;
    margin-bottom: 0.8rem;
    line-height: 1.8;
}
.ask-error {
    background: #fdf3f3;
    border: 1px solid #e8c4c4;
    border-radius: 6px;
    padding: 0.65rem 1rem;
    font-size: 0.81rem;
    color: #8b3030;
    margin-bottom: 0.8rem;
}

/* ── AI chart suggestion ── */
.ai-chart-suggestion { background:#fafaf8; border:1px solid #e8e5df; border-radius:6px; padding:0.8rem 1rem; margin-bottom:1rem; font-size:0.81rem; color:#555555; line-height:1.5; }
.ai-chart-suggestion strong { color:#1c1c1c; }

/* ── Relationships ── */
.join-header { background:#ffffff; border:1px solid #e8e5df; border-radius:6px; padding:1.2rem 1.4rem; margin-bottom:0.5rem; }
.join-title { font-family:'DM Serif Display',serif; font-size:1.15rem; color:#1c1c1c; margin-bottom:0.3rem; letter-spacing:-0.01em; }
.join-meta-row { display:flex; align-items:center; gap:1.2rem; flex-wrap:wrap; margin-top:0.4rem; }
.join-meta-item { font-family:'DM Mono',monospace; font-size:0.68rem; color:#888888; }
.join-meta-item span { color:#3d3d3d; font-weight:500; }
.join-key-badge { font-family:'DM Mono',monospace; font-size:0.68rem; color:#3d3d3d; background:#f2f2f2; border-radius:3px; padding:2px 7px; }

/* ── Cleaning / DQ ── */
.clean-card { background:#ffffff; border:1px solid #e8e5df; border-radius:6px; padding:1rem 1.2rem; margin-bottom:0.6rem; }
.clean-stat { font-family:'DM Mono',monospace; font-size:0.72rem; color:#666666; margin-bottom:0.25rem; }
.clean-stat strong { color:#1c1c1c; }
.dq-ok { background:#f0f7f0; border:1px solid #c4dcc4; border-radius:6px; padding:0.9rem 1.1rem; font-size:0.84rem; color:#3d7a3d; }
.dq-error { background:#fdf3f3; border:1px solid #e8c4c4; border-radius:6px; padding:0.65rem 1rem; margin-bottom:0.4rem; font-size:0.81rem; color:#8b3030; }
.dq-warning { background:#fdf9f0; border:1px solid #e8dcc0; border-radius:6px; padding:0.65rem 1rem; margin-bottom:0.4rem; font-size:0.81rem; color:#7a5a20; }

/* ── Downloads ── */
[data-testid="stDownloadButton"]>button { background:#ffffff!important; border:1px solid #d8d4ce!important; border-radius:5px!important; color:#4a4a4a!important; font-family:'DM Mono',monospace!important; font-size:0.73rem!important; padding:0.45rem 0.9rem!important; transition:all 0.15s!important; width:100%!important; }
[data-testid="stDownloadButton"]>button:hover { border-color:#3d3d3d!important; color:#1c1c1c!important; background:#f5f4f2!important; }

/* ── Controls ── */
[data-testid="stSelectbox"]>div>div { background:#ffffff!important; border:1px solid #d8d4ce!important; border-radius:5px!important; color:#1c1c1c!important; }
[data-testid="stDataFrame"] { border-radius:6px; border:1px solid #e8e5df!important; }
[data-testid="stSuccess"] { background:#f0f7f0!important; border:1px solid #c4dcc4!important; border-radius:6px!important; color:#3d7a3d!important; }
[data-testid="stExpander"] { background:#ffffff!important; border:1px solid #e8e5df!important; border-radius:6px!important; }
[data-testid="stExpander"] summary { font-family:'DM Sans',sans-serif!important; font-weight:500!important; color:#4a4a4a!important; font-size:0.84rem!important; }
hr { border-color:#e8e5df!important; }
[data-testid="stSpinner"] p { color:#3d3d3d!important; }

/* ── Footer ── */
.footer {
    margin-top: 4rem;
    padding-top: 1.5rem;
    border-top: 1px solid #e8e5df;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.5rem;
}
.footer-left {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    color: #888888;
    letter-spacing: 0.04em;
}
.footer-left a {
    color: #3d3d3d;
    text-decoration: none;
    border-bottom: 1px solid #cccccc;
    padding-bottom: 1px;
    transition: border-color 0.15s;
}
.footer-left a:hover { border-color: #3d3d3d; }
.footer-right {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: #aaaaaa;
}

/* ── Sample data button ── */
.sample-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    color: #888888;
    margin: 0.5rem 0 0.3rem 0;
    letter-spacing: 0.04em;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────
def to_dict(obj):
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return obj


def load_validated_df(file_info: dict) -> pd.DataFrame | None:
    path = file_info.get("validated_path")
    if not path or not Path(path).exists():
        return None
    return pd.read_csv(path)


def metric_card(label: str, value: str, style: str = "") -> str:
    return (
        f'<div class="metric-card">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value {style}">{value}</div>'
        f'</div>'
    )


def section(label: str):
    st.markdown(f'<div class="section-header">{label}</div>', unsafe_allow_html=True)


def tab_header(title: str, desc: str):
    st.markdown(f'<div class="tab-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="tab-desc">{desc}</div>', unsafe_allow_html=True)


def styled_plotly(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#fafafa",
        font=dict(family="DM Sans", color="#4a4a4a", size=11),
        title_font=dict(family="DM Serif Display", color="#1c1c1c", size=14),
        xaxis=dict(gridcolor="#eeebe6", color="#888888", linecolor="#e8e5df"),
        yaxis=dict(gridcolor="#eeebe6", color="#888888", linecolor="#e8e5df"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#4a4a4a")),
        margin=dict(t=50, b=40, l=40, r=20),
        colorway=["#2C4A6E", "#C4622D", "#4A7C59", "#8C5E3C", "#5B7FA6", "#B85C3A"],
    )
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=True)
    return fig


def parse_insights(raw: str) -> dict:
    """Parse LLM JSON output, return dict with fallback."""
    try:
        return json.loads(raw)
    except Exception:
        return {"summary": raw}


def get_ai_chart_suggestions(df: pd.DataFrame, file_name: str, numeric_cols: list, categorical_cols: list) -> list[dict]:
    """Ask GPT to suggest 2-3 meaningful charts given the dataset structure."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return []
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        sample_stats = {}
        for col in numeric_cols[:6]:
            sample_stats[col] = {
                "mean": round(float(df[col].mean()), 2),
                "std": round(float(df[col].std()), 2),
                "min": round(float(df[col].min()), 2),
                "max": round(float(df[col].max()), 2),
            }
        cat_counts = {col: df[col].nunique() for col in categorical_cols[:6]}

        prompt = f"""You are a data analyst. Given this dataset, suggest 2-3 specific, meaningful charts.

Dataset: {file_name}
Rows: {len(df)}
Numeric columns with stats: {json.dumps(sample_stats)}
Categorical columns with unique counts: {json.dumps(cat_counts)}

Return ONLY a JSON array. No markdown, no backticks.
Each item must have:
- "chart_type": one of "Bar Chart", "Histogram", "Scatter Plot", "Box Plot", "Line Chart", "Correlation Heatmap"
- "x": column name for x axis (or null)
- "y": column name for y axis (or null)
- "color": column name to color by (or null)
- "top_n": integer if bar chart (default 10), else null
- "reason": one sentence explaining what this chart reveals

Only suggest columns that exist. Make suggestions specific and insightful — not generic."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600,
        )
        raw = response.choices[0].message.content.strip()
        return json.loads(raw)
    except Exception:
        return []


def render_suggested_chart(df: pd.DataFrame, suggestion: dict):
    """Render a chart from an AI suggestion dict."""
    chart_type = suggestion.get("chart_type", "")
    x = suggestion.get("x")
    y = suggestion.get("y")
    color = suggestion.get("color")
    top_n = suggestion.get("top_n", 10)

    try:
        if chart_type == "Bar Chart" and x:
            counts = df[x].value_counts().head(top_n or 10).reset_index()
            counts.columns = [x, "count"]
            fig = px.bar(counts, x=x, y="count", title=f"Top {top_n or 10}: {x}", color_discrete_sequence=["#2C4A6E"])
        elif chart_type == "Histogram" and x:
            fig = px.histogram(df, x=x, title=f"Distribution: {x}", color_discrete_sequence=["#2C4A6E"])
        elif chart_type == "Scatter Plot" and x and y:
            fig = px.scatter(df, x=x, y=y, color=color if color and color in df.columns else None,
                             title=f"{y} vs {x}")
        elif chart_type == "Box Plot" and y:
            fig = px.box(df, y=y, x=x if x and x in df.columns else None,
                         color=x if x and x in df.columns else None, title=f"Box Plot: {y}")
        elif chart_type == "Line Chart" and x and y:
            temp = df.copy()
            try:
                temp[x] = pd.to_datetime(temp[x])
                temp = temp.sort_values(x)
            except Exception:
                pass
            fig = px.line(temp, x=x, y=y, title=f"{y} over {x}", markers=True)
        elif chart_type == "Correlation Heatmap":
            num_cols = df.select_dtypes(include="number").columns.tolist()
            if len(num_cols) >= 2:
                corr = df[num_cols[:8]].corr()
                fig = px.imshow(corr, text_auto=True, title="Correlation Heatmap",
                                aspect="auto", color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
            else:
                return
        else:
            return
        st.plotly_chart(styled_plotly(fig), use_container_width=True, theme=None, key=f"sug_{id(fig)}")
    except Exception as e:
        st.caption(f"Could not render chart: {e}")



def ask_data_question(df: pd.DataFrame, question: str, file_name: str) -> dict:
    """
    Send a natural language question about a dataframe to GPT-4o-mini.
    Returns dict with keys: answer, chart (optional plotly fig), error.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OPENAI_API_KEY not set."}

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        schema = {
            "file": file_name,
            "rows": len(df),
            "columns": {
                col: {
                    "dtype": str(df[col].dtype),
                    "sample": df[col].dropna().head(3).tolist(),
                    "nunique": int(df[col].nunique()),
                }
                for col in df.columns
            }
        }

        prompt = f"""You are a data analyst. A user is asking a question about a dataset.
Your job is to answer it by writing a single Pandas expression and providing a plain-English answer.

Dataset schema:
{json.dumps(schema, indent=2)}

User question: {question}

Return ONLY a JSON object with these keys:
{{
  "answer": "Plain-English answer in 1-3 sentences. Be specific — use actual numbers, column names, values from the data.",
  "pandas_expr": "A single Python expression using the variable `df` that computes the answer. Must be a valid expression that returns a value, Series, or DataFrame. No assignments, no multi-line code.",
  "chart_type": "bar" | "line" | "histogram" | "scatter" | null,
  "chart_x": "column name or null",
  "chart_y": "column name or null",
  "chart_color": "column name or null"
}}

Rules:
- pandas_expr must be a single expression, not a statement. Use .head(20) if it might return many rows.
- Only reference columns that actually exist in the schema above.
- If the question cannot be answered from this data, set pandas_expr to null and explain in answer.
- chart_type should be null if a table or scalar answer is more appropriate than a chart.
- Do not use f-strings or complex lambdas in pandas_expr.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500,
        )

        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)

        result = {"answer": data.get("answer", ""), "chart": None, "error": None, "table": None}

        expr = data.get("pandas_expr")
        if expr:
            try:
                computed = eval(expr, {"df": df, "pd": pd})
                if isinstance(computed, pd.DataFrame):
                    result["table"] = computed.head(20)
                elif isinstance(computed, pd.Series):
                    result["table"] = computed.reset_index().head(20)
                else:
                    # scalar — fold into answer
                    result["answer"] = result["answer"] + f" (computed: {computed})"
            except Exception as e:
                result["error"] = f"Could not execute expression: {e}"

        # Build chart if requested
        chart_type = data.get("chart_type")
        cx = data.get("chart_x")
        cy = data.get("chart_y")
        cc = data.get("chart_color")

        if chart_type and cx and cx in df.columns:
            try:
                if chart_type == "bar" and cy and cy in df.columns:
                    fig = px.bar(df.groupby(cx)[cy].sum().reset_index().sort_values(cy, ascending=False).head(20),
                                 x=cx, y=cy, title=f"{cy} by {cx}", color_discrete_sequence=["#2C4A6E"])
                    result["chart"] = fig
                elif chart_type == "bar":
                    counts = df[cx].value_counts().head(20).reset_index()
                    counts.columns = [cx, "count"]
                    fig = px.bar(counts, x=cx, y="count", title=f"Top values: {cx}", color_discrete_sequence=["#2C4A6E"])
                    result["chart"] = fig
                elif chart_type == "line" and cy and cy in df.columns:
                    temp = df[[cx, cy]].dropna().copy()
                    try:
                        temp[cx] = pd.to_datetime(temp[cx])
                        temp = temp.sort_values(cx)
                    except Exception:
                        pass
                    fig = px.line(temp, x=cx, y=cy, title=f"{cy} over {cx}", markers=True, color_discrete_sequence=["#2C4A6E"])
                    result["chart"] = fig
                elif chart_type == "histogram":
                    fig = px.histogram(df, x=cx, title=f"Distribution: {cx}", color_discrete_sequence=["#2C4A6E"])
                    result["chart"] = fig
                elif chart_type == "scatter" and cy and cy in df.columns:
                    fig = px.scatter(df, x=cx, y=cy,
                                     color=cc if cc and cc in df.columns else None,
                                     title=f"{cy} vs {cx}")
                    result["chart"] = fig
            except Exception:
                pass  # chart is optional, don't fail

        return result

    except json.JSONDecodeError:
        return {"error": "GPT returned an unexpected response. Try rephrasing your question.", "answer": "", "chart": None, "table": None}
    except Exception as e:
        return {"error": str(e), "answer": "", "chart": None, "table": None}


# ── Hero ───────────────────────────────────────────────────────────────────────
PIPELINE_STEPS = ["Ingest", "Clean", "Validate", "Detect Relationships", "Analyze", "AI Insights"]
steps_html = "".join(
    f'<span class="pipeline-step">{s}</span>' + ('<span class="pipeline-arrow">→</span>' if i < len(PIPELINE_STEPS) - 1 else "")
    for i, s in enumerate(PIPELINE_STEPS)
)

st.markdown(f"""
<div class="hero-section">
    <div class="hero-eyebrow">Multi-Agent Data Analyst</div>
    <div class="hero-title">Upload data.<br><em>Get answers.</em></div>
    <div class="hero-desc">
        Drop any combination of <strong>CSVs or Excel files</strong> (sales records, logs, relational tables, time series, survey exports) and a six-agent pipeline automatically cleans, validates, joins related datasets,
        computes statistics, and delivers <strong>AI-generated insights with specific next steps</strong>.
        No code. No configuration. Built for analysts and engineers who want signal fast.
    </div>
    <div class="value-props">
        <div class="value-prop">
            <div class="value-prop-label">Auto cleaning</div>
            <div class="value-prop-text">Rename columns, duplicate removal, missing value detection. Fully logged.</div>
        </div>
        <div class="value-prop">
            <div class="value-prop-label">Relationship detection</div>
            <div class="value-prop-text">Finds join keys across files, executes merges, and surfaces cross-dataset patterns</div>
        </div>
        <div class="value-prop">
            <div class="value-prop-label">AI insights + chart suggestions</div>
            <div class="value-prop-text">GPT-4o-mini interprets the data and recommends what to investigate next</div>
        </div>
    </div>
    <div class="pipeline-row">{steps_html}</div>
</div>
""", unsafe_allow_html=True)

# ── Sample data paths ─────────────────────────────────────────────────────────
SAMPLE_DIR = PROJECT_ROOT / "sample_data"
SAMPLE_FILES = [
    "Candy_Sales.csv",
    "Candy_Products.csv",
    "Candy_Factories.csv",
    "Candy_Targets.csv",
]

# ── Upload ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="upload-label">Upload your datasets (up to 5 CSV or Excel files)</div>', unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Upload",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

# Sample data row
col_sample_label, col_sample_btn, _ = st.columns([2, 1, 4])
with col_sample_label:
    st.markdown('<div class="sample-label">No data? Try the built-in sample:</div>', unsafe_allow_html=True)
with col_sample_btn:
    load_sample = st.button("Load Sample Data", use_container_width=True, key="load_sample")

if load_sample:
    st.session_state["use_sample"] = True
    st.session_state.pop("pipeline_result", None)
    st.session_state.pop("ai_charts", None)

use_sample = st.session_state.get("use_sample", False) and not uploaded_files

if uploaded_files:
    st.session_state.pop("use_sample", None)
    use_sample = False

if uploaded_files:
    if len(uploaded_files) > 5:
        st.markdown('<div class="dq-error">Maximum 5 files. Please remove some and try again.</div>', unsafe_allow_html=True)
        st.stop()
    file_names = "  ·  ".join(f.name for f in uploaded_files)
    st.markdown(f'<div class="files-ready">✓  {len(uploaded_files)} file(s) ready: {file_names}</div>', unsafe_allow_html=True)

if use_sample:
    sample_names = "  ·  ".join(SAMPLE_FILES)
    st.markdown(f'<div class="files-ready">✓  Sample dataset loaded: {sample_names}</div>', unsafe_allow_html=True)

run_input_paths = None
if uploaded_files or use_sample:
    col_btn, _ = st.columns([1, 5])
    with col_btn:
        run = st.button("Run Analysis", use_container_width=True)

    if run:
        if use_sample:
            input_paths = [SAMPLE_DIR / f for f in SAMPLE_FILES if (SAMPLE_DIR / f).exists()]
            state = init_state(input_paths=input_paths)
            graph = build_graph()
            with st.spinner("Running pipeline…"):
                final_state = graph.invoke(state)
            st.session_state["pipeline_result"] = to_dict(final_state)
        else:
            with tempfile.TemporaryDirectory() as tmpdir:
                input_paths = []
                for uploaded in uploaded_files:
                    path = Path(tmpdir) / uploaded.name
                    path.write_bytes(uploaded.getbuffer())
                    input_paths.append(path)
                state = init_state(input_paths=input_paths)
                graph = build_graph()
                with st.spinner("Running pipeline…"):
                    final_state = graph.invoke(state)
                st.session_state["pipeline_result"] = to_dict(final_state)

# ── Results ────────────────────────────────────────────────────────────────────
if "pipeline_result" in st.session_state:
    result = st.session_state["pipeline_result"]
    files = [to_dict(f) for f in result["files"]]
    validation_report = to_dict(result["validation_report"])
    issues = [to_dict(i) for i in validation_report.get("issues", [])]
    status = result["status"]

    if status == "failed":
        st.markdown(
            '<div class="dq-error" style="margin:1rem 0;font-size:0.84rem;">'
            'Pipeline failed. Validation errors could not be resolved. See Data Quality for details.</div>',
            unsafe_allow_html=True,
        )

    (tab_ai, tab_overview, tab_dq, tab_clean,
     tab_rel, tab_analysis, tab_dl) = st.tabs([
        "AI Insights", "Overview", "Data Quality",
        "Cleaning Log", "Relationships", "Analysis", "Downloads",
    ])

    # ── AI Insights ────────────────────────────────────────────────────────────
    with tab_ai:
        tab_header(
            "AI Insights",
            "GPT-4o-mini reads every agent's output and returns structured findings, "
            "data quality observations, specific next steps, and risks to watch. "
            "Written the way a senior analyst would summarize a data review.",
        )
        raw_insights = result.get("llm_insights", "")
        if not raw_insights:
            st.markdown('<div class="dq-warning">No insights generated. Set OPENAI_API_KEY in your .env file.</div>', unsafe_allow_html=True)
        else:
            data = parse_insights(raw_insights)
            if "error" in data:
                st.markdown(f'<div class="dq-warning">⚠ {data["error"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="ai-label">Generated by GPT-4o-mini · LangGraph pipeline</div>', unsafe_allow_html=True)

                if data.get("summary"):
                    st.markdown(f'<div class="ai-summary">{data["summary"]}</div>', unsafe_allow_html=True)

                if data.get("findings"):
                    st.markdown('<div class="ai-section-title">Key Findings</div>', unsafe_allow_html=True)
                    bullets_html = "".join(
                        f'<div class="ai-bullet"><div class="ai-bullet-dot"></div><span>{b}</span></div>'
                        for b in data["findings"]
                    )
                    st.markdown(f'<div class="ai-bullets">{bullets_html}</div>', unsafe_allow_html=True)

                if data.get("data_quality"):
                    st.markdown('<div class="ai-section-title">Data Quality</div>', unsafe_allow_html=True)
                    bullets_html = "".join(
                        f'<div class="ai-bullet"><div class="ai-bullet-dot"></div><span>{b}</span></div>'
                        for b in data["data_quality"]
                    )
                    st.markdown(f'<div class="ai-bullets">{bullets_html}</div>', unsafe_allow_html=True)

                if data.get("recommendations"):
                    st.markdown('<div class="ai-section-title">Recommended Next Steps</div>', unsafe_allow_html=True)
                    bullets_html = "".join(
                        f'<div class="ai-bullet"><div class="ai-rec-dot"></div><span>{b}</span></div>'
                        for b in data["recommendations"]
                    )
                    st.markdown(f'<div class="ai-bullets">{bullets_html}</div>', unsafe_allow_html=True)

                if data.get("watch_out_for"):
                    st.markdown('<div class="ai-section-title">Watch Out For</div>', unsafe_allow_html=True)
                    bullets_html = "".join(
                        f'<div class="ai-bullet"><div class="ai-warn-dot"></div><span>{b}</span></div>'
                        for b in data["watch_out_for"]
                    )
                    st.markdown(f'<div class="ai-bullets">{bullets_html}</div>', unsafe_allow_html=True)

    # ── Overview ───────────────────────────────────────────────────────────────
    with tab_overview:
        tab_header(
            "Overview",
            "A summary of this pipeline run: files processed, row counts, "
            "validation status, and any errors or warnings detected.",
        )
        val_passed = validation_report.get("passed", False)
        errors = [i for i in issues if i["severity"] == "error"]
        warnings = [i for i in issues if i["severity"] == "warning"]

        st.markdown(
            '<div class="metric-grid">'
            + metric_card("Files", str(len(files)))
            + metric_card("Total Rows", f'{sum(f["row_count"] for f in files):,}')
            + metric_card("Validation", "Passed" if val_passed else "Failed", "green" if val_passed else "red")
            + metric_card("Errors", str(len(errors)), "red" if errors else "muted")
            + metric_card("Warnings", str(len(warnings)), "muted")
            + metric_card("Status", status.capitalize(), "green" if status == "complete" else "red")
            + '</div>',
            unsafe_allow_html=True,
        )

        section("Files")
        for file in files:
            cols_html = "".join(f'<span class="col-chip">{c}</span>' for c in file["columns"][:24])
            overflow = (
                f'<span class="col-chip" style="color:#3d3d3d;background:#e8e8e8;">+{len(file["columns"])-24} more</span>'
                if len(file["columns"]) > 24 else ""
            )
            st.markdown(
                f'<div class="file-card">'
                f'<div class="file-card-name">{file["original_name"]}</div>'
                f'<div class="file-card-meta">{file["row_count"]:,} rows · {file["column_count"]} columns</div>'
                f'<div>{cols_html}{overflow}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Data Quality ───────────────────────────────────────────────────────────
    with tab_dq:
        tab_header(
            "Data Quality",
            "The validation agent checks every cleaned file for structural problems: "
            "empty datasets and columns with over 50% missing values. "
            "Errors stop the pipeline. Warnings are flagged but don't block analysis.",
        )
        if not issues:
            st.markdown('<div class="dq-ok">✓ All files passed validation. No errors or warnings found.</div>', unsafe_allow_html=True)
        else:
            errors_list = [i for i in issues if i["severity"] == "error"]
            warnings_list = [i for i in issues if i["severity"] == "warning"]
            if errors_list:
                section(f"Errors ({len(errors_list)})")
                for issue in errors_list:
                    col_note = f" · {issue['column']}" if issue.get("column") else ""
                    st.markdown(f'<div class="dq-error"><strong>{issue["file_id"]}{col_note}</strong>: {issue["message"]}</div>', unsafe_allow_html=True)
            if warnings_list:
                section(f"Warnings ({len(warnings_list)})")
                for issue in warnings_list:
                    col_note = f" · {issue['column']}" if issue.get("column") else ""
                    st.markdown(f'<div class="dq-warning"><strong>{issue["file_id"]}{col_note}</strong>: {issue["message"]}</div>', unsafe_allow_html=True)

    # ── Cleaning Log ───────────────────────────────────────────────────────────
    with tab_clean:
        tab_header(
            "Cleaning Log",
            "The cleaning agent removes duplicate rows, strips whitespace, and standardizes "
            "column names. Any columns that were renamed are shown explicitly. "
            "Every transformation is logged here for full transparency.",
        )
        cleaning_logs = result.get("cleaning_logs", {})
        if not cleaning_logs:
            st.markdown('<div class="tab-desc">No cleaning logs available.</div>', unsafe_allow_html=True)
        else:
            for _, log in cleaning_logs.items():
                orig_cols = log["original_columns"]
                clean_cols = log["cleaned_columns"]
                renamed = [(o, c) for o, c in zip(orig_cols, clean_cols) if o != c]
                clean_chips = "".join(f'<span class="col-chip">{c}</span>' for c in clean_cols)
                rename_html = ""
                if renamed:
                    rows_html = "".join(
                        f'<span class="col-chip" style="text-decoration:line-through;opacity:0.5;">{o}</span>'
                        f'<span style="color:#888888;font-size:0.65rem;margin:0 3px;">→</span>'
                        f'<span class="col-chip">{c}</span>  '
                        for o, c in renamed
                    )
                    rename_html = f'<div style="margin-top:0.7rem;"><div class="section-header" style="margin-top:0.5rem;">Renamed columns ({len(renamed)})</div>{rows_html}</div>'
                st.markdown(
                    f'<div class="clean-card">'
                    f'<div class="file-card-name">{log["original_name"]}</div>'
                    f'<div style="margin-top:0.4rem;">'
                    f'<span class="clean-stat">Duplicates removed: <strong>{log["duplicates_removed"]}</strong></span>'
                    f'&nbsp;&nbsp;<span class="clean-stat">Columns: <strong>{len(clean_cols)}</strong></span>'
                    f'</div>'
                    f'{rename_html}'
                    f'<div style="margin-top:0.7rem;"><div class="section-header" style="margin-top:0.5rem;">Final columns</div>{clean_chips}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── Relationships ──────────────────────────────────────────────────────────
    with tab_rel:
        tab_header(
            "Relationships",
            "The relationship agent detects shared columns across files and executes inner joins "
            "on the best candidate key. Cross-dataset analysis runs on the merged result, "
            "surfacing patterns neither file alone would reveal.",
        )
        relationships = result.get("relationship_results", {}).get("relationships", [])
        if not relationships:
            st.markdown(
                '<div class="tab-desc" style="color:#666666;">No shared columns detected. '
                'Upload related tables (e.g. orders + customers sharing a customer_id) to see join suggestions.</div>',
                unsafe_allow_html=True,
            )
        else:
            for idx, rel in enumerate(relationships):
                join_rows = rel.get("join_rows")
                join_rows_str = f"{join_rows:,}" if isinstance(join_rows, int) else "—"
                shared_str = ", ".join(rel["shared_columns"])
                st.markdown(
                    f'<div class="join-header">'
                    f'<div class="join-title">{rel["file_a"]}  ×  {rel["file_b"]}</div>'
                    f'<div class="join-meta-row">'
                    f'<span class="join-meta-item">Join key: <span><span class="join-key-badge">{rel["suggested_join_key"]}</span></span></span>'
                    f'<span class="join-meta-item">Matched rows: <span>{join_rows_str}</span></span>'
                    f'<span class="join-meta-item">Shared columns: <span>{shared_str}</span></span>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
                if rel.get("join_error"):
                    st.markdown(f'<div class="dq-error">Join error: {rel["join_error"]}</div>', unsafe_allow_html=True)
                if rel.get("cross_dataset_insights"):
                    section("Cross-dataset insights")
                    insights_html = "".join(
                        f'<div class="insight-row"><div class="insight-dot"></div>{ins}</div>'
                        for ins in rel["cross_dataset_insights"]
                    )
                    st.markdown(
                        f'<div style="background:#ffffff;border:1px solid #e8e5df;border-radius:6px;padding:0.4rem 1rem;margin-bottom:1rem;">{insights_html}</div>',
                        unsafe_allow_html=True,
                    )
                col_dl1, col_dl2, _ = st.columns([1, 1, 3])
                with col_dl1:
                    fp = rel.get("full_join_path")
                    if fp and Path(fp).exists():
                        with open(fp, "rb") as f:
                            st.download_button("↓ Full join CSV", f, Path(fp).name, "text/csv",
                                               key=f"rel_full_{idx}", use_container_width=True)
                with col_dl2:
                    pp = rel.get("join_preview_path")
                    if pp and Path(pp).exists():
                        with open(pp, "rb") as f:
                            st.download_button("↓ Preview (100 rows)", f, Path(pp).name, "text/csv",
                                               key=f"rel_prev_{idx}", use_container_width=True)
                if idx < len(relationships) - 1:
                    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Analysis ───────────────────────────────────────────────────────────────
    with tab_analysis:
        tab_header(
            "Analysis",
            "Statistical summary, AI-suggested charts for this dataset, and a chart builder "
            "where you can explore any column combination yourself.",
        )
        analysis_results = result.get("analysis_results", {})
        if not analysis_results:
            st.markdown('<div class="tab-desc">No analysis results found.</div>', unsafe_allow_html=True)
        else:
            file_labels = {a["file_name"]: fid for fid, a in analysis_results.items()}
            selected_name = st.selectbox("File", list(file_labels.keys()), label_visibility="visible")
            analysis = analysis_results[file_labels[selected_name]]
            matching_file = next(f for f in files if f["original_name"] == analysis["file_name"])
            df = load_validated_df(matching_file)

            st.markdown(
                '<div class="metric-grid">'
                + metric_card("Rows", f'{analysis["row_count"]:,}')
                + metric_card("Columns", str(analysis["column_count"]))
                + metric_card("Numeric", str(len(analysis.get("numeric_columns", []))))
                + metric_card("Categorical", str(len(analysis.get("categorical_columns", []))))
                + '</div>',
                unsafe_allow_html=True,
            )

            if analysis.get("insights"):
                section("Statistical Summary")
                insights_html = "".join(
                    f'<div class="insight-row"><div class="insight-dot"></div>{ins}</div>'
                    for ins in analysis["insights"]
                )
                st.markdown(
                    f'<div style="background:#ffffff;border:1px solid #e8e5df;border-radius:6px;padding:0.4rem 1rem;margin-bottom:1rem;">{insights_html}</div>',
                    unsafe_allow_html=True,
                )

            if df is not None:
                numeric_cols = analysis.get("numeric_columns", [])
                categorical_cols = analysis.get("categorical_columns", [])
                all_cols = analysis.get("columns", [])

                section("Data Preview")
                st.dataframe(df.head(20), use_container_width=True, height=260)

                # ── Ask anything ─────────────────────────────────────────────
                section("Ask a Question")
                st.markdown(
                    '<div class="ask-example">Try: "Which product has the highest gross profit?" &nbsp;·&nbsp; '
                    '"Show sales by region" &nbsp;·&nbsp; "What is the average order value?" &nbsp;·&nbsp; '
                    '"Is there a trend in order date vs sales?"</div>',
                    unsafe_allow_html=True,
                )

                ask_col, ask_btn_col = st.columns([5, 1])
                with ask_col:
                    user_question = st.text_input(
                        "Question",
                        placeholder="Ask anything about this dataset…",
                        label_visibility="collapsed",
                        key=f"ask_input_{selected_name}",
                    )
                with ask_btn_col:
                    ask_run = st.button("Ask", use_container_width=True, key=f"ask_btn_{selected_name}")

                if ask_run and user_question.strip():
                    with st.spinner("Thinking…"):
                        ask_result = ask_data_question(df, user_question.strip(), selected_name)
                    st.session_state[f"ask_result_{selected_name}"] = ask_result

                ask_result = st.session_state.get(f"ask_result_{selected_name}")
                if ask_result:
                    if ask_result.get("error"):
                        st.markdown(f'<div class="ask-error">{ask_result["error"]}</div>', unsafe_allow_html=True)
                    if ask_result.get("answer"):
                        st.markdown(f'<div class="ask-result-answer">{ask_result["answer"]}</div>', unsafe_allow_html=True)
                    if ask_result.get("table") is not None:
                        st.dataframe(ask_result["table"], use_container_width=True)
                    if ask_result.get("chart") is not None:
                        st.plotly_chart(styled_plotly(ask_result["chart"]), use_container_width=True, theme=None,
                                        key=f"ask_chart_{selected_name}_{user_question[:20]}")

                # ── AI suggested charts ──────────────────────────────────────
                section("AI-Suggested Charts")
                cache_key = f"ai_charts_{selected_name}"
                if cache_key not in st.session_state:
                    with st.spinner("Asking GPT to suggest charts…"):
                        st.session_state[cache_key] = get_ai_chart_suggestions(
                            df, selected_name, numeric_cols, categorical_cols
                        )
                suggestions = st.session_state.get(cache_key, [])

                if not suggestions:
                    st.markdown('<div class="tab-desc" style="color:#888888;">No suggestions available. Set OPENAI_API_KEY to enable.</div>', unsafe_allow_html=True)
                else:
                    for i, sug in enumerate(suggestions):
                        reason = sug.get("reason", "")
                        chart_label = f'{sug.get("chart_type", "Chart")}: {sug.get("y") or sug.get("x", "")}'
                        st.markdown(
                            f'<div class="ai-chart-suggestion"><strong>{chart_label}</strong>: {reason}</div>',
                            unsafe_allow_html=True,
                        )
                        render_suggested_chart(df, sug)

                # ── Chart builder ────────────────────────────────────────────
                section("Chart Builder")
                st.markdown(
                    '<div class="chart-builder-callout">'
                    '<span style="font-size:1.1rem;">🔍</span>'
                    '<div class="chart-builder-callout-text">'
                    '<strong>Your turn.</strong> Pick any column combination below to build your own chart. '
                    'Use this to validate the AI suggestions or explore hypotheses of your own.'
                    '</div></div>',
                    unsafe_allow_html=True,
                )

                chart_col, opts_col = st.columns([3, 1])
                with opts_col:
                    chart_type = st.selectbox("Chart type", [
                        "Bar Chart", "Histogram", "Scatter Plot",
                        "Box Plot", "Line Chart", "Correlation Heatmap",
                    ])

                with chart_col:
                    if chart_type == "Histogram":
                        if numeric_cols:
                            with opts_col:
                                x_col = st.selectbox("Column", numeric_cols)
                            fig = px.histogram(df, x=x_col, title=f"Distribution: {x_col}", color_discrete_sequence=["#2C4A6E"])
                            st.plotly_chart(styled_plotly(fig), use_container_width=True, theme=None, key=f"cb_hist_{selected_name}_{x_col}")
                        else:
                            st.warning("No numeric columns.")

                    elif chart_type == "Bar Chart":
                        if categorical_cols:
                            with opts_col:
                                x_col = st.selectbox("Column", categorical_cols)
                                top_n = st.slider("Top N", 5, 30, 10)
                            counts = df[x_col].value_counts().head(top_n).reset_index()
                            counts.columns = [x_col, "count"]
                            fig = px.bar(counts, x=x_col, y="count", title=f"Top {top_n}: {x_col}", color_discrete_sequence=["#2C4A6E"])
                            st.plotly_chart(styled_plotly(fig), use_container_width=True, theme=None, key=f"cb_bar_{selected_name}_{x_col}_{top_n}")
                        else:
                            st.warning("No categorical columns.")

                    elif chart_type == "Scatter Plot":
                        if len(numeric_cols) >= 2:
                            with opts_col:
                                x_col = st.selectbox("X axis", numeric_cols)
                                y_col = st.selectbox("Y axis", [c for c in numeric_cols if c != x_col])
                                color_col = st.selectbox("Color by", ["None"] + categorical_cols)
                            fig = px.scatter(df, x=x_col, y=y_col,
                                             color=None if color_col == "None" else color_col,
                                             title=f"{y_col} vs {x_col}")
                            st.plotly_chart(styled_plotly(fig), use_container_width=True, theme=None, key=f"cb_scatter_{selected_name}_{x_col}_{y_col}")
                        else:
                            st.warning("Need at least 2 numeric columns.")

                    elif chart_type == "Box Plot":
                        if numeric_cols:
                            with opts_col:
                                y_col = st.selectbox("Numeric column", numeric_cols)
                                x_col = st.selectbox("Group by", ["None"] + categorical_cols)
                            fig = px.box(df, y=y_col,
                                         x=None if x_col == "None" else x_col,
                                         color=None if x_col == "None" else x_col,
                                         title=f"Box Plot: {y_col}")
                            st.plotly_chart(styled_plotly(fig), use_container_width=True, theme=None, key=f"cb_box_{selected_name}_{y_col}_{x_col}")
                        else:
                            st.warning("No numeric columns.")

                    elif chart_type == "Line Chart":
                        if all_cols and numeric_cols:
                            with opts_col:
                                x_col = st.selectbox("X axis", all_cols)
                                y_col = st.selectbox("Y axis", numeric_cols)
                            temp_df = df.copy()
                            try:
                                temp_df[x_col] = pd.to_datetime(temp_df[x_col])
                                temp_df = temp_df.sort_values(x_col)
                            except Exception:
                                pass
                            fig = px.line(temp_df, x=x_col, y=y_col,
                                          title=f"{y_col} over {x_col}", markers=True, color_discrete_sequence=["#2C4A6E"])
                            st.plotly_chart(styled_plotly(fig), use_container_width=True, theme=None, key=f"cb_line_{selected_name}_{x_col}_{y_col}")
                        else:
                            st.warning("Need at least 1 numeric column.")

                    elif chart_type == "Correlation Heatmap":
                        if len(numeric_cols) >= 2:
                            with opts_col:
                                sel = st.multiselect("Columns", numeric_cols, default=numeric_cols[:min(6, len(numeric_cols))])
                            if len(sel) >= 2:
                                corr = df[sel].corr()
                                fig = px.imshow(corr, text_auto=True, title="Correlation Heatmap",
                                                aspect="auto", color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
                                st.plotly_chart(styled_plotly(fig), use_container_width=True, theme=None, key="cb_heatmap_{}_{}".format(selected_name, "_".join(sel)))
                            else:
                                st.warning("Select at least 2 columns.")
                        else:
                            st.warning("Need at least 2 numeric columns.")

    # ── Downloads ──────────────────────────────────────────────────────────────
    with tab_dl:
        tab_header(
            "Downloads",
            "Export any file the pipeline produced. Cleaned files have standardized column names "
            "and duplicates removed. Validated files are the final pre-analysis stage. "
            "Full joins are the executed merges from the relationship agent.",
        )
        relationships_dl = result.get("relationship_results", {}).get("relationships", [])
        dl_sections = [
            ("Cleaned files", [(f["original_name"], f.get("cleaned_path"), f"dl_c_{f['original_name']}") for f in files]),
            ("Validated files", [(f["original_name"], f.get("validated_path"), f"dl_v_{f['original_name']}") for f in files]),
            ("Full joins", [
                (f"{r['file_a']} × {r['file_b']}", r.get("full_join_path"), f"dl_j_{i}")
                for i, r in enumerate(relationships_dl)
            ]),
        ]
        for sec_name, items in dl_sections:
            available = [(n, p, k) for n, p, k in items if p and Path(p).exists()]
            if not available:
                continue
            section(sec_name)
            cols = st.columns(min(len(available), 3))
            for i, (name, path, key) in enumerate(available):
                with cols[i % 3]:
                    with open(path, "rb") as f:
                        st.download_button(f"↓ {name}", f, Path(path).name, "text/csv",
                                           key=key, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    <div class="footer-left">
        Built by <a href="https://ananyaa-tanwar.github.io/" target="_blank">Ananyaa Tanwar</a>
        &nbsp;·&nbsp; MS Information Management, UIUC
        &nbsp;·&nbsp; Data Engineering &amp; Analytics
    </div>
    <div class="footer-right">Multi-Agent Data Analyst · LangGraph + GPT-4o-mini</div>
</div>
""", unsafe_allow_html=True)