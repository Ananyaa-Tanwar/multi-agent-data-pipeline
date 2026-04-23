from __future__ import annotations

from typing import Literal

from langgraph.graph import StateGraph, END

from src.core.state import PipelineState
from src.agents.ingestion import ingest_node
from src.agents.cleaner import clean_node
from src.agents.validator import validate_node
from src.agents.analyst import analyze_node
from src.agents.relationship import relationship_node


def route_after_validation(state: PipelineState) -> Literal["relationships", "clean", "stop"]:
    if state.validation_report.passed:
        return "relationships"

    if state.retry_count < state.max_retries:
        state.retry_count += 1
        return "clean"

    state.status = "failed"
    return "stop"


def build_graph():
    g = StateGraph(PipelineState)

    g.add_node("ingest", ingest_node)
    g.add_node("clean", clean_node)
    g.add_node("validate", validate_node)
    g.add_node("relationships", relationship_node)
    g.add_node("analyze", analyze_node)

    g.set_entry_point("ingest")

    g.add_edge("ingest", "clean")
    g.add_edge("clean", "validate")

    g.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "relationships": "relationships",
            "clean": "clean",
            "stop": END,
        },
    )

    g.add_edge("relationships", "analyze")
    g.add_edge("analyze", END)

    return g.compile()