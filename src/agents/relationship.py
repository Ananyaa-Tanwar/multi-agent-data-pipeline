from __future__ import annotations

from itertools import combinations

import pandas as pd

from src.core.state import PipelineState


def relationship_node(state: PipelineState) -> PipelineState:
    relationships = []

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
        }

        if file_a.validated_path and file_b.validated_path:
            df_a = pd.read_csv(file_a.validated_path)
            df_b = pd.read_csv(file_b.validated_path)

            try:
                joined = df_a.merge(df_b, on=suggested_join_key, how="inner")

                preview_path = (
                    state.run_dir
                    / "reports"
                    / f"join_preview_{file_a.file_id}_{file_b.file_id}.csv"
                )
                joined.head(100).to_csv(preview_path, index=False)

                relationship["join_rows"] = len(joined)
                relationship["join_preview_path"] = str(preview_path)

            except Exception as e:
                relationship["join_error"] = str(e)

        relationships.append(relationship)

    state.relationship_results = {"relationships": relationships}
    return state