from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.io as pio
import streamlit as st

from src.core.artifacts import init_state
from src.graph.pipeline_graph import build_graph

pio.templates.default = "plotly_white"


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


st.set_page_config(page_title="Multi-Agent Data Analyst", layout="wide")

st.title("Multi-Agent Data Analyst")
st.caption("LangGraph-powered multi-file data cleaning, validation, relationship detection, and analysis.")

uploaded_files = st.file_uploader(
    "Upload 1–5 CSV or Excel files",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=True,
)

if uploaded_files:
    if len(uploaded_files) > 5:
        st.error("Please upload at most 5 files.")
        st.stop()

    st.write(f"{len(uploaded_files)} file(s) uploaded.")

    if st.button("Run analysis"):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_paths = []

            for uploaded in uploaded_files:
                path = Path(tmpdir) / uploaded.name
                path.write_bytes(uploaded.getbuffer())
                input_paths.append(path)

            state = init_state(input_paths=input_paths)
            graph = build_graph()

            with st.spinner("Running multi-agent pipeline..."):
                final_state = graph.invoke(state)

            st.session_state["pipeline_result"] = to_dict(final_state)

if "pipeline_result" in st.session_state:
    result = st.session_state["pipeline_result"]

    files = [to_dict(f) for f in result["files"]]
    validation_report = to_dict(result["validation_report"])
    issues = [to_dict(i) for i in validation_report.get("issues", [])]

    st.success("Pipeline complete.")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["Overview", "Data Quality", "Cleaning Log", "Relationships", "Analysis", "Downloads"]
    )

    with tab1:
        st.subheader("Overview")

        c1, c2, c3 = st.columns(3)
        c1.metric("Files processed", len(files))
        c2.metric("Validation passed", str(validation_report["passed"]))
        c3.metric("Status", result["status"])

        st.write("Run directory:", result["run_dir"])

        for file in files:
            st.markdown(f"### {file['original_name']}")
            st.write(f"{file['row_count']} rows, {file['column_count']} columns")
            st.caption(f"Columns: {', '.join(file['columns'])}")

    with tab2:
        st.subheader("Data Quality")

        if issues:
            st.dataframe(issues, use_container_width=True)
        else:
            st.info("No validation issues found.")

    with tab3:
        st.subheader("Cleaning Log")

        cleaning_logs = result.get("cleaning_logs", {})

        if cleaning_logs:
            for _, log in cleaning_logs.items():
                st.markdown(f"### {log['original_name']}")
                st.write("Duplicates removed:", log["duplicates_removed"])
                st.write("Original columns:", log["original_columns"])
                st.write("Cleaned columns:", log["cleaned_columns"])
        else:
            st.info("No cleaning logs available.")

    with tab4:
        st.subheader("Detected Relationships")

        relationships = result.get("relationship_results", {}).get("relationships", [])

        if relationships:
            st.dataframe(relationships, use_container_width=True)

            for rel in relationships:
                st.markdown(
                    f"**{rel['file_a']} + {rel['file_b']}** using `{rel['suggested_join_key']}`"
                )
                st.write("Join rows:", rel.get("join_rows"))

                preview_path = rel.get("join_preview_path")
                if preview_path and Path(preview_path).exists():
                    with open(preview_path, "rb") as f:
                        st.download_button(
                            label=f"Download join preview: {rel['file_a']} + {rel['file_b']}",
                            data=f,
                            file_name=Path(preview_path).name,
                            mime="text/csv",
                        )
        else:
            st.info("No shared columns detected between files.")

    with tab5:
        st.subheader("Analysis Results")

        analysis_results = result.get("analysis_results", {})

        if not analysis_results:
            st.info("No analysis results found.")
        else:
            file_labels = {
                analysis["file_name"]: file_id
                for file_id, analysis in analysis_results.items()
            }

            selected_file_name = st.selectbox("Select file to analyze", list(file_labels.keys()))
            selected_file_id = file_labels[selected_file_name]
            analysis = analysis_results[selected_file_id]

            matching_file = next(
                f for f in files if f["original_name"] == analysis["file_name"]
            )
            df = load_validated_df(matching_file)

            st.markdown(f"## {analysis['file_name']}")

            c1, c2 = st.columns(2)
            c1.metric("Rows", analysis["row_count"])
            c2.metric("Columns", analysis["column_count"])

            if analysis.get("insights"):
                st.markdown("### Key Insights")
                for insight in analysis["insights"]:
                    st.info(insight)

            if df is not None:
                numeric_cols = analysis.get("numeric_columns", [])
                categorical_cols = analysis.get("categorical_columns", [])
                all_cols = analysis.get("columns", [])

                st.markdown("### Data Preview")
                st.dataframe(df.head(20), use_container_width=True)

                st.markdown("### Dynamic Chart Builder")

                chart_type = st.selectbox(
                    "Choose chart type",
                    [
                        "Histogram",
                        "Bar Chart",
                        "Scatter Plot",
                        "Box Plot",
                        "Line Chart",
                        "Correlation Heatmap",
                    ],
                )

                if chart_type == "Histogram":
                    if numeric_cols:
                        x_col = st.selectbox("Numeric column", numeric_cols)
                        fig = px.histogram(
                            df,
                            x=x_col,
                            title=f"Distribution of {x_col}",
                            color_discrete_sequence=["#636EFA"],
                        )
                        st.plotly_chart(fig, use_container_width=True, theme=None)
                    else:
                        st.warning("No numeric columns available.")

                elif chart_type == "Bar Chart":
                    if categorical_cols:
                        x_col = st.selectbox("Categorical column", categorical_cols)
                        top_n = st.slider("Top N values", 5, 30, 10)
                        counts = df[x_col].value_counts().head(top_n).reset_index()
                        counts.columns = [x_col, "count"]

                        fig = px.bar(
                            counts,
                            x=x_col,
                            y="count",
                            title=f"Top {top_n} values in {x_col}",
                            color="count",
                            color_continuous_scale="Blues",
                        )
                        st.plotly_chart(fig, use_container_width=True, theme=None)
                    else:
                        st.warning("No categorical columns available.")

                elif chart_type == "Scatter Plot":
                    if len(numeric_cols) >= 2:
                        x_col = st.selectbox("X-axis", numeric_cols)
                        y_col = st.selectbox(
                            "Y-axis",
                            [c for c in numeric_cols if c != x_col],
                        )

                        color_col = st.selectbox(
                            "Optional color column",
                            ["None"] + categorical_cols,
                        )

                        fig = px.scatter(
                            df,
                            x=x_col,
                            y=y_col,
                            color=None if color_col == "None" else color_col,
                            title=f"{y_col} vs {x_col}",
                        )
                        st.plotly_chart(fig, use_container_width=True, theme=None)
                    else:
                        st.warning("Need at least two numeric columns.")

                elif chart_type == "Box Plot":
                    if numeric_cols:
                        y_col = st.selectbox("Numeric column", numeric_cols)
                        x_options = ["None"] + categorical_cols
                        x_col = st.selectbox("Optional category column", x_options)

                        fig = px.box(
                            df,
                            y=y_col,
                            x=None if x_col == "None" else x_col,
                            title=f"Box Plot of {y_col}",
                            color=None if x_col == "None" else x_col,
                        )
                        st.plotly_chart(fig, use_container_width=True, theme=None)
                    else:
                        st.warning("No numeric columns available.")

                elif chart_type == "Line Chart":
                    if all_cols and numeric_cols:
                        x_col = st.selectbox("X-axis column", all_cols)
                        y_col = st.selectbox("Y-axis numeric column", numeric_cols)

                        temp_df = df.copy()
                        try:
                            temp_df[x_col] = pd.to_datetime(temp_df[x_col])
                            temp_df = temp_df.sort_values(x_col)
                        except Exception:
                            pass

                        fig = px.line(
                            temp_df,
                            x=x_col,
                            y=y_col,
                            title=f"{y_col} over {x_col}",
                            markers=True,
                        )
                        st.plotly_chart(fig, use_container_width=True, theme=None)
                    else:
                        st.warning("Need at least one numeric column.")

                elif chart_type == "Correlation Heatmap":
                    if len(numeric_cols) >= 2:
                        selected_numeric = st.multiselect(
                            "Select numeric columns",
                            numeric_cols,
                            default=numeric_cols[: min(5, len(numeric_cols))],
                        )

                        if len(selected_numeric) >= 2:
                            corr = df[selected_numeric].corr()
                            fig = px.imshow(
                                corr,
                                text_auto=True,
                                title="Correlation Heatmap",
                                aspect="auto",
                                color_continuous_scale="RdBu_r",
                            )
                            st.plotly_chart(fig, use_container_width=True, theme=None)
                        else:
                            st.warning("Select at least two numeric columns.")
                    else:
                        st.warning("Need at least two numeric columns.")

                st.markdown("### Auto-Generated Saved Charts")
                for chart_path in analysis["charts"]:
                    chart_file = Path(chart_path)
                    if chart_file.exists():
                        st.components.v1.html(
                            chart_file.read_text(),
                            height=500,
                            scrolling=True,
                        )

    with tab6:
        st.subheader("Downloads")

        st.write("Run directory:", result["run_dir"])

        st.markdown("### Cleaned Files")
        for file in files:
            cleaned_path = file.get("cleaned_path")
            if cleaned_path and Path(cleaned_path).exists():
                with open(cleaned_path, "rb") as f:
                    st.download_button(
                        label=f"Download cleaned {file['original_name']}",
                        data=f,
                        file_name=Path(cleaned_path).name,
                        mime="text/csv",
                    )

        st.markdown("### Validated Files")
        for file in files:
            validated_path = file.get("validated_path")
            if validated_path and Path(validated_path).exists():
                with open(validated_path, "rb") as f:
                    st.download_button(
                        label=f"Download validated {file['original_name']}",
                        data=f,
                        file_name=Path(validated_path).name,
                        mime="text/csv",
                    )