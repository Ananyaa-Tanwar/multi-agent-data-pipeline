from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd

from src.core.state import PipelineState


def _cross_dataset_insights(joined: pd.DataFrame, file_a_name: str, file_b_name: str, join_key: str) -> list[str]:
    """Generate insights from a merged dataset that neither file alone would surface."""
    insights = []

    numeric_cols = joined.select_dtypes(include="number").columns.tolist()
    # Exclude the join key itself if it's numeric
    numeric_cols = [c for c in numeric_cols if c != join_key]

    if len(numeric_cols) >= 2:
        corr = joined[numeric_cols].corr()
        mask = ~np.eye(corr.shape[0], dtype=bool)
        pairs = corr.where(mask).stack()
        if not pairs.empty:
            strongest = pairs.abs().idxmax()
            val = corr.loc[strongest[0], strongest[1]]
            insights.append(
                f"After joining on `{join_key}`, strongest cross-file correlation is between "
                f"`{strongest[0]}` and `{strongest[1]}` ({val:.2f})."
            )

    for col in numeric_cols[:3]:
        mean_val = joined[col].mean()
        std_val = joined[col].std()
        insights.append(
            f"In the joined dataset, `{col}` has mean {mean_val:.2f} and std {std_val:.2f}."
        )

    categorical_cols = joined.select_dtypes(include=["object", "category"]).columns.tolist()
    categorical_cols = [c for c in categorical_cols if c != join_key]
    for col in categorical_cols[:2]:
        top_val = joined[col].value_counts().idxmax()
        top_count = joined[col].value_counts().max()
        insights.append(
            f"In the joined dataset, most common `{col}` is '{top_val}' ({top_count} records)."
        )

    return insights


def relationship_node(state: PipelineState) -> PipelineState:
    relationships = []
    all_cross_insights = []

    for file_a, file_b in combinations(state.files, 2):
        shared_columns = sorted(set(file_a.columns).intersection(set(file_b.columns)))

        if not shared_columns:
            continue

        suggested_join_key = shared_columns[0]

        relationship = {
            "file_a": file_a.original_name,
            "file_b": file_b.original_name,
            "shared_columns": shared_columns,
            "suggested_join_key": suggested_join_key,
            "join_rows": None,
            "join_preview_path": None,
            "full_join_path": None,
            "cross_dataset_insights": [],
        }

        if file_a.validated_path and file_b.validated_path:
            df_a = pd.read_csv(file_a.validated_path)
            df_b = pd.read_csv(file_b.validated_path)

            try:
                joined = df_a.merge(df_b, on=suggested_join_key, how="inner")

                # Preview (100 rows) — for download tab
                preview_path = (
                    state.run_dir
                    / "reports"
                    / f"join_preview_{file_a.file_id}_{file_b.file_id}.csv"
                )
                joined.head(100).to_csv(preview_path, index=False)

                # Full join — for analysis and download
                full_join_path = (
                    state.run_dir
                    / "reports"
                    / f"join_full_{file_a.file_id}_{file_b.file_id}.csv"
                )
                joined.to_csv(full_join_path, index=False)

                # Cross-dataset insights
                cross_insights = _cross_dataset_insights(
                    joined, file_a.original_name, file_b.original_name, suggested_join_key
                )

                relationship["join_rows"] = len(joined)
                relationship["join_preview_path"] = str(preview_path)
                relationship["full_join_path"] = str(full_join_path)
                relationship["cross_dataset_insights"] = cross_insights
                all_cross_insights.extend(cross_insights)

            except Exception as e:
                relationship["join_error"] = str(e)

        relationships.append(relationship)

    state.relationship_results = {
        "relationships": relationships,
        "cross_dataset_insights": all_cross_insights,
    }
    return state