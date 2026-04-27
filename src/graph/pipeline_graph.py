from __future__ import annotations

import os
from typing import Literal

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from src.core.state import PipelineState
from src.agents.ingestion import ingest_node
from src.agents.cleaner import clean_node
from src.agents.validator import validate_node
from src.agents.analyst import analyze_node
from src.agents.relationship import relationship_node
from src.agents.schema_drift import schema_drift_node
from src.agents.llm_insights import llm_insights_node

load_dotenv()

# LangSmith tracing — enable by setting these in your .env file:
#   LANGCHAIN_TRACING_V2=true
#   LANGCHAIN_API_KEY=your_langsmith_key
#   LANGCHAIN_PROJECT=multi-agent-data-pipeline
# No code changes needed — LangGraph picks these up automatically from env.


def route_after_validation(state: PipelineState) -> Literal["schema_drift", "clean", "stop"]:
    if state.validation_report.passed:
        return "schema_drift"

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
    g.add_node("schema_drift", schema_drift_node)
    g.add_node("relationships", relationship_node)
    g.add_node("analyze", analyze_node)
    g.add_node("llm_insights", llm_insights_node)

    g.set_entry_point("ingest")

    g.add_edge("ingest", "clean")
    g.add_edge("clean", "validate")

    g.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "schema_drift": "schema_drift",
            "clean": "clean",
            "stop": END,
        },
    )

    g.add_edge("schema_drift", "relationships")
    g.add_edge("relationships", "analyze")
    g.add_edge("analyze", "llm_insights")
    g.add_edge("llm_insights", END)

    return g.compile()