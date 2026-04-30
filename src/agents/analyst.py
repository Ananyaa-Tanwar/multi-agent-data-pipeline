from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio

from src.core.state import PipelineState

pio.templates.default = "plotly_white"

CHART_PRIMARY = "#2C4A6E"
CHART_PALETTE = ["#2C4A6E", "#C4622D", "#4A7C59", "#8C5E3C", "#5B7FA6", "#B85C3A"]

METRIC_KEYWORDS = [
    "revenue", "profit", "sales", "amount", "quantity", "qty",
    "price", "cost", "total", "gross", "net", "units", "count", "value",
]

DATE_KEYWORDS = ["date", "time", "month", "year", "day", "period", "week"]


def style_fig(fig):
    fig.update_layout(
        template="plotly_white",
        plot_bgcolor="#fafafa",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color="#4a4a4a", size=11),
        title_font=dict(family="DM Sans, sans-serif", color="#1c1c1c", size=13),
        margin=dict(t=50, b=40, l=40, r=20),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#4a4a4a")),
        colorway=CHART_PALETTE,
    )
    fig.update_xaxes(showgrid=True, gridcolor="#eeebe6", color="#888888", linecolor="#e8e5df")
    fig.update_yaxes(showgrid=True, gridcolor="#eeebe6", color="#888888", linecolor="#e8e5df")
    return fig


def find_metric_cols(numeric_cols: list[str]) -> list[str]:
    """Return numeric cols that look like metrics, in priority order."""
    hits = []
    for kw in METRIC_KEYWORDS:
        for c in numeric_cols:
            if kw in c.lower() and c not in hits:
                hits.append(c)
    # Append remaining numeric cols that weren't matched
    for c in numeric_cols:
        if c not in hits:
            hits.append(c)
    return hits


def find_date_col(df: pd.DataFrame) -> str | None:
    """Return the first column that looks like a date."""
    for col in df.columns:
        if any(kw in col.lower() for kw in DATE_KEYWORDS):
            try:
                pd.to_datetime(df[col].dropna().head(20))
                return col
            except Exception:
                continue
    return None


def analyze_node(state: PipelineState) -> PipelineState:
    analysis_results = {}

    for file in state.files:
        if not file.validated_path:
            continue

        df = pd.read_csv(file.validated_path)

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        metric_cols = find_metric_cols(numeric_cols)
        date_col = find_date_col(df)

        file_results = {
            "file_name": file.original_name,
            "validated_path": str(file.validated_path),
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "summary_stats": df.describe(include="all").fillna("").to_dict(),
            "charts": [],
            "insights": [],
        }

        # ── Insights: only surface meaningful ones ─────────────────────────
        # For metric columns: show sum and mean (more useful than min/max for business data)
        for col in metric_cols[:4]:
            total = df[col].sum()
            mean = df[col].mean()
            if total > 1000:
                file_results["insights"].append(
                    f"{col}: total is {total:,.0f}, average per row is {mean:,.2f}."
                )
            else:
                file_results["insights"].append(
                    f"{col}: average is {mean:.2f}, min is {df[col].min():.2f}, max is {df[col].max():.2f}."
                )

        # For categorical columns: cardinality and top value
        for col in categorical_cols[:4]:
            counts = df[col].value_counts(dropna=False)
            if not counts.empty:
                pct = counts.iloc[0] / len(df) * 100
                file_results["insights"].append(
                    f"{col}: {df[col].nunique()} unique values. "
                    f"Most common is '{counts.index[0]}' ({pct:.0f}% of rows)."
                )

        # Correlation insight
        if len(numeric_cols) >= 2:
            corr_df = df[numeric_cols].apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")
            if corr_df.shape[1] >= 2:
                corr = corr_df.corr().fillna(0)
                corr_pairs = corr.where(~np.eye(corr.shape[0], dtype=bool)).stack()
                if not corr_pairs.empty:
                    strongest_pair = corr_pairs.abs().idxmax()
                    strongest_value = corr.loc[strongest_pair[0], strongest_pair[1]]
                    if abs(strongest_value) > 0.3:
                        direction = "positive" if strongest_value > 0 else "negative"
                        file_results["insights"].append(
                            f"Strongest {direction} relationship is between "
                            f"{strongest_pair[0]} and {strongest_pair[1]} "
                            f"(r = {strongest_value:.2f})."
                        )

        # ── Auto charts ────────────────────────────────────────────────────

        # 1. For each top categorical col: bar chart of metric sum (not count)
        primary_metric = metric_cols[0] if metric_cols else None
        for cat_col in categorical_cols[:2]:
            if primary_metric:
                # Metric by category
                agg = df.groupby(cat_col)[primary_metric].sum().reset_index()
                agg = agg.sort_values(primary_metric, ascending=False).head(15)
                fig = px.bar(
                    agg, x=cat_col, y=primary_metric,
                    title=f"Total {primary_metric} by {cat_col}",
                    color_discrete_sequence=[CHART_PRIMARY],
                )
            else:
                # Fallback: frequency count
                counts = df[cat_col].value_counts().head(15).reset_index()
                counts.columns = [cat_col, "count"]
                fig = px.bar(
                    counts, x=cat_col, y="count",
                    title=f"Top values: {cat_col}",
                    color_discrete_sequence=[CHART_PRIMARY],
                )
            fig.update_traces(marker_line_color="white", marker_line_width=1)
            fig = style_fig(fig)
            chart_path = state.run_dir / "charts" / f"{file.file_id}_{cat_col}_bar.html"
            fig.write_html(chart_path)
            file_results["charts"].append(str(chart_path))

        # 2. If there are 2+ categorical cols: stacked bar (metric by cat1 colored by cat2)
        if len(categorical_cols) >= 2 and primary_metric:
            cat1, cat2 = categorical_cols[0], categorical_cols[1]
            agg = df.groupby([cat1, cat2])[primary_metric].sum().reset_index()
            top_cats = df.groupby(cat1)[primary_metric].sum().nlargest(10).index.tolist()
            agg = agg[agg[cat1].isin(top_cats)]
            fig = px.bar(
                agg, x=cat1, y=primary_metric, color=cat2,
                title=f"Total {primary_metric} by {cat1}, broken down by {cat2}",
                barmode="stack",
            )
            fig = style_fig(fig)
            chart_path = state.run_dir / "charts" / f"{file.file_id}_{cat1}_{cat2}_stacked.html"
            fig.write_html(chart_path)
            file_results["charts"].append(str(chart_path))

        # 3. Distribution histogram for primary metric
        if primary_metric:
            fig = px.histogram(
                df, x=primary_metric,
                title=f"Distribution: {primary_metric}",
                nbins=40,
                color_discrete_sequence=[CHART_PRIMARY],
            )
            fig.update_traces(marker_line_color="white", marker_line_width=1)
            fig = style_fig(fig)
            chart_path = state.run_dir / "charts" / f"{file.file_id}_{primary_metric}_hist.html"
            fig.write_html(chart_path)
            file_results["charts"].append(str(chart_path))

        # 4. Time series if a date column exists
        if date_col and primary_metric:
            try:
                ts = df.copy()
                ts[date_col] = pd.to_datetime(ts[date_col])
                ts = ts.groupby(pd.Grouper(key=date_col, freq="ME"))[primary_metric].sum().reset_index()
                ts = ts.dropna()
                if len(ts) >= 3:
                    fig = px.line(
                        ts, x=date_col, y=primary_metric,
                        title=f"{primary_metric} over time",
                        markers=True,
                        color_discrete_sequence=[CHART_PRIMARY],
                    )
                    fig = style_fig(fig)
                    chart_path = state.run_dir / "charts" / f"{file.file_id}_{primary_metric}_timeseries.html"
                    fig.write_html(chart_path)
                    file_results["charts"].append(str(chart_path))
            except Exception:
                pass

        # 5. Correlation heatmap for numeric cols
        if len(numeric_cols) >= 2:
            corr_df = df[numeric_cols].apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")
            if corr_df.shape[1] >= 2:
                corr = corr_df.corr().fillna(0)
                fig = px.imshow(
                    corr,
                    text_auto=".2f",
                    title="Correlation Heatmap",
                    aspect="auto",
                    color_continuous_scale="RdBu_r",
                    zmin=-1,
                    zmax=1,
                )
                fig = style_fig(fig)
                chart_path = state.run_dir / "charts" / f"{file.file_id}_correlation_heatmap.html"
                fig.write_html(chart_path)
                file_results["charts"].append(str(chart_path))

        analysis_results[file.file_id] = file_results

    state.analysis_results = analysis_results
    state.status = "complete"
    return state