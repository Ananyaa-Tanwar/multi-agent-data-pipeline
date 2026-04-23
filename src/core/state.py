from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FileArtifact(BaseModel):
    file_id: str
    original_name: str
    raw_path: Path
    cleaned_path: Optional[Path] = None
    validated_path: Optional[Path] = None
    row_count: int = 0
    column_count: int = 0
    columns: List[str] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    file_id: str
    severity: str  # info | warning | error
    column: Optional[str] = None
    check: str
    message: str


class ValidationReport(BaseModel):
    passed: bool = False
    issues: List[ValidationIssue] = Field(default_factory=list)


class PipelineState(BaseModel):
    run_id: str
    run_dir: Path

    input_paths: List[Path] = Field(default_factory=list)
    files: List[FileArtifact] = Field(default_factory=list)

    validation_report: ValidationReport = Field(default_factory=ValidationReport)

    cleaning_logs: Dict[str, Any] = Field(default_factory=dict)
    analysis_results: Dict[str, Any] = Field(default_factory=dict)
    relationship_results: Dict[str, Any] = Field(default_factory=dict)

    retry_count: int = 0
    max_retries: int = 1
    status: str = "initialized"