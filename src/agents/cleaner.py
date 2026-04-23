from __future__ import annotations

import pandas as pd

from src.core.file_utils import read_table, clean_column_name
from src.core.state import PipelineState


def clean_node(state: PipelineState) -> PipelineState:
    cleaning_logs = {}

    for file in state.files:
        df = read_table(file.raw_path)

        original_columns = list(df.columns)
        df.columns = [clean_column_name(c) for c in df.columns]

        before_rows = len(df)
        df = df.drop_duplicates()
        after_rows = len(df)

        cleaned_path = state.run_dir / "cleaned" / f"{file.file_id}_cleaned.csv"
        df.to_csv(cleaned_path, index=False)

        file.cleaned_path = cleaned_path
        file.row_count = len(df)
        file.column_count = len(df.columns)
        file.columns = list(df.columns)

        cleaning_logs[file.file_id] = {
            "original_name": file.original_name,
            "original_columns": original_columns,
            "cleaned_columns": list(df.columns),
            "duplicates_removed": before_rows - after_rows,
            "cleaned_path": str(cleaned_path),
        }

    state.cleaning_logs = cleaning_logs
    return state