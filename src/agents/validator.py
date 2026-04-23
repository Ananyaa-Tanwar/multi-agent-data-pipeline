from __future__ import annotations

import pandas as pd

from src.core.state import PipelineState, ValidationIssue, ValidationReport


def validate_node(state: PipelineState) -> PipelineState:
    issues = []

    for file in state.files:
        if not file.cleaned_path:
            issues.append(
                ValidationIssue(
                    file_id=file.file_id,
                    severity="error",
                    column=None,
                    check="cleaned_file_exists",
                    message="Cleaned file was not created.",
                )
            )
            continue

        df = pd.read_csv(file.cleaned_path)

        if df.empty:
            issues.append(
                ValidationIssue(
                    file_id=file.file_id,
                    severity="error",
                    column=None,
                    check="non_empty_dataset",
                    message="Dataset is empty after cleaning.",
                )
            )

        for col in df.columns:
            missing_pct = df[col].isna().mean()

            if missing_pct > 0.5:
                issues.append(
                    ValidationIssue(
                        file_id=file.file_id,
                        severity="warning",
                        column=col,
                        check="missing_values",
                        message=f"Column has {missing_pct:.1%} missing values.",
                    )
                )

        validated_path = state.run_dir / "validated" / f"{file.file_id}_validated.csv"
        df.to_csv(validated_path, index=False)
        file.validated_path = validated_path

    has_errors = any(issue.severity == "error" for issue in issues)

    state.validation_report = ValidationReport(
        passed=not has_errors,
        issues=issues,
    )

    return state