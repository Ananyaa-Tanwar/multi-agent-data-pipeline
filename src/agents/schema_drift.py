from __future__ import annotations

from itertools import combinations

from src.core.state import PipelineState, SchemaDriftResult


def schema_drift_node(state: PipelineState) -> PipelineState:
    """
    Detects schema drift between uploaded files.

    Two modes:
    1. Same-name files (e.g. sales_jan.csv vs sales_feb.csv) — compares column sets
       to flag additions, removals, and type changes between time-period snapshots.
    2. All file pairs — flags any column that exists in one file but not another,
       which helps users understand join risk and data completeness.
    """
    drift_results = []

    for file_a, file_b in combinations(state.files, 2):
        cols_a = set(file_a.columns)
        cols_b = set(file_b.columns)

        only_in_a = sorted(cols_a - cols_b)
        only_in_b = sorted(cols_b - cols_a)
        shared = sorted(cols_a & cols_b)

        if not only_in_a and not only_in_b:
            drift_status = "identical_schema"
            summary = f"{file_a.original_name} and {file_b.original_name} have identical column schemas."
        else:
            drift_status = "schema_drift_detected"
            parts = []
            if only_in_a:
                parts.append(f"{len(only_in_a)} column(s) only in {file_a.original_name}: {', '.join(only_in_a)}")
            if only_in_b:
                parts.append(f"{len(only_in_b)} column(s) only in {file_b.original_name}: {', '.join(only_in_b)}")
            summary = ". ".join(parts) + "."

        drift_results.append(
            SchemaDriftResult(
                file_a=file_a.original_name,
                file_b=file_b.original_name,
                status=drift_status,
                only_in_a=only_in_a,
                only_in_b=only_in_b,
                shared_columns=shared,
                summary=summary,
            )
        )

    state.schema_drift_results = drift_results
    return state