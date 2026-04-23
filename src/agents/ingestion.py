from __future__ import annotations

from src.core.file_utils import read_table
from src.core.state import FileArtifact, PipelineState


def ingest_node(state: PipelineState) -> PipelineState:
    files = []

    for i, path in enumerate(state.input_paths, start=1):
        df = read_table(path)

        file_artifact = FileArtifact(
            file_id=f"file_{i}",
            original_name=path.name,
            raw_path=path,
            row_count=len(df),
            column_count=len(df.columns),
            columns=list(df.columns),
        )
        files.append(file_artifact)

    state.files = files
    return state