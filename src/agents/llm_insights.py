from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env", override=True)

from openai import OpenAI

from src.core.state import PipelineState

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY is not set. Add it to your .env file.")
        _client = OpenAI(api_key=api_key)
    return _client


def _build_prompt(analysis_results: dict, relationship_results: dict, validation_report: dict) -> str:
    lines = []
    lines.append(
        "You are a senior data engineer and analyst reviewing a multi-file dataset analysis. "
        "Return ONLY a valid JSON object. No markdown, no backticks, no preamble.\n"
    )

    lines.append("## Data context\n")
    for file_id, result in analysis_results.items():
        lines.append(f"### {result['file_name']}")
        lines.append(f"- Shape: {result['row_count']} rows x {result['column_count']} columns")
        lines.append(f"- Numeric columns: {', '.join(result['numeric_columns']) or 'none'}")
        lines.append(f"- Categorical columns: {', '.join(result['categorical_columns']) or 'none'}")
        lines.append("- Statistical findings:")
        for ins in result.get("insights", []):
            lines.append(f"  - {ins}")

    rels = relationship_results.get("relationships", [])
    if rels:
        lines.append("\n## Relationships detected")
        for rel in rels:
            lines.append(
                f"- {rel['file_a']} × {rel['file_b']} joined on `{rel['suggested_join_key']}` "
                f"({rel.get('join_rows', '?')} matched rows)"
            )
        cross = relationship_results.get("cross_dataset_insights", [])
        for c in cross:
            lines.append(f"  - {c}")

    issues = validation_report.get("issues", [])
    if issues:
        lines.append("\n## Data quality issues")
        for issue in issues:
            col = f" [{issue['column']}]" if issue.get("column") else ""
            lines.append(f"- [{issue['severity'].upper()}] {issue['file_id']}{col}: {issue['message']}")

    lines.append("""
## Your task

Return a JSON object with exactly these keys:

{
  "summary": "2-3 sentence plain-English overview of what this data is and what was found. Be specific: mention actual column names, row counts, or values where relevant.",
  "findings": [
    "Bullet point finding 1. Specific and quantified where possible, written as a data analyst would say it",
    "Bullet point finding 2",
    ...
  ],
  "data_quality": [
    "One bullet per notable data quality observation (missing values, duplicates removed, type issues, sparse columns). Skip this array if no issues.",
    ...
  ],
  "recommendations": [
    "Specific next step a data analyst or engineer should take. E.g. 'Investigate the correlation between X and Y using a scatter plot grouped by Z', 'Check for seasonality in the date column', 'The join on customer_id has 40% row loss, verify referential integrity'",
    ...
  ],
  "watch_out_for": [
    "One bullet per risk or caveat. E.g. skewed distributions, potential outliers, columns that may need normalization, join key collisions, time gaps in series data",
    ...
  ]
}

Rules:
- findings: 4-6 bullets, each specific and data-grounded. No generic observations.
- data_quality: omit empty array if no issues. Max 4 bullets.
- recommendations: 3-5 actionable next steps. Reference actual column names.
- watch_out_for: 2-4 risk flags. Be candid.
- All bullets: concise, direct. Write how a senior analyst talks in a PR comment, not a report.
- Vary across relational tables, time series, flat files. Do not assume the data type.
""")

    return "\n".join(lines)


def llm_insights_node(state: PipelineState) -> PipelineState:
    if not state.analysis_results:
        state.llm_insights = "{}"
        return state

    try:
        client = _get_client()
        prompt = _build_prompt(
            state.analysis_results,
            state.relationship_results,
            state.validation_report.model_dump() if hasattr(state.validation_report, "model_dump") else state.validation_report,
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1200,
        )

        raw = response.choices[0].message.content.strip()
        # Validate it parses, store raw JSON string
        json.loads(raw)
        state.llm_insights = raw

    except EnvironmentError as e:
        state.llm_insights = json.dumps({"error": str(e)})
    except json.JSONDecodeError:
        # Model returned non-JSON, store raw as summary fallback
        state.llm_insights = json.dumps({"summary": response.choices[0].message.content.strip()})
    except Exception as e:
        state.llm_insights = json.dumps({"error": str(e)})

    return state