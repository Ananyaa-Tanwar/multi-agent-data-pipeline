from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio

from src.core.state import PipelineState

pio.templates.default = "plotly_white"

CHART_BLUE = "#636EFA"
CHART_TEAL = "#00CC96"


def style_fig(fig):
    fig.update_layout(
        template="plotly_white",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="#222222"),
        title_font=dict(color="#222222"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#E5E5E5", color="#222222")
    fig.update_yaxes(showgrid=True, gridcolor="#E5E5E5", color="#222222")
    return fig


def analyze_node(state: PipelineState) -> PipelineState:
    analysis_results = {}

    for file in state.files:
        if not file.validated_path:
            continue

        df = pd.read_csv(file.validated_path)

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

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

        for col in numeric_cols:
            file_results["insights"].append(
                f"{col}: average is {df[col].mean():.2f}, min is {df[col].min():.2f}, max is {df[col].max():.2f}."
            )

        for col in categorical_cols:
            counts = df[col].value_counts(dropna=False)
            if not counts.empty:
                file_results["insights"].append(
                    f"{col}: most common value is '{counts.index[0]}' with {counts.iloc[0]} records."
                )

        for col in numeric_cols[:3]:
            fig = px.histogram(df, x=col, title=f"Distribution of {col}")
            fig.update_traces(
                marker_color=CHART_BLUE,
                marker_line_color="white",
                marker_line_width=1,
            )
            fig = style_fig(fig)

            chart_path = state.run_dir / "charts" / f"{file.file_id}_{col}_hist.html"
            fig.write_html(chart_path)
            file_results["charts"].append(str(chart_path))

        for col in categorical_cols[:3]:
            counts = df[col].value_counts().reset_index()
            counts.columns = [col, "count"]

            fig = px.bar(
                counts.head(10),
                x=col,
                y="count",
                title=f"Top values in {col}",
            )
            fig.update_traces(
                marker_color=CHART_TEAL,
                marker_line_color="white",
                marker_line_width=1,
            )
            fig = style_fig(fig)

            chart_path = state.run_dir / "charts" / f"{file.file_id}_{col}_bar.html"
            fig.write_html(chart_path)
            file_results["charts"].append(str(chart_path))

        # Correlation heatmap - outside numeric/categorical loops
        if len(numeric_cols) >= 2:
            corr_df = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
            corr_df = corr_df.dropna(axis=1, how="all")

            if corr_df.shape[1] >= 2:
                corr = corr_df.corr().fillna(0)

                fig = px.imshow(
                    corr,
                    text_auto=True,
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

                corr_pairs = corr.where(~np.eye(corr.shape[0], dtype=bool)).stack()
                if not corr_pairs.empty:
                    strongest_pair = corr_pairs.abs().idxmax()
                    strongest_value = corr.loc[strongest_pair[0], strongest_pair[1]]
                    file_results["insights"].append(
                        f"Strongest numeric relationship is between {strongest_pair[0]} and {strongest_pair[1]} "
                        f"with correlation {strongest_value:.2f}."
                    )

        analysis_results[file.file_id] = file_results

    state.analysis_results = analysis_results
    state.status = "complete"
    return state