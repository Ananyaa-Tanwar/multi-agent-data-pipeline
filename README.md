# Multi-Agent Data Analyst (LangGraph + Streamlit)

**Try the app:** https://multi-agent-data-pipeline-ananyaa.streamlit.app/

> Upload your datasets and get automated cleaning, validation, relationship detection, and AI-powered insights.

An end-to-end **multi-agent data analysis system** that ingests multiple datasets, performs automated cleaning and validation, detects relationships across files, and generates both statistical and **LLM-powered insights**.

Built using **LangGraph for orchestration** and **Streamlit for an interactive UI**.

---

## Overview

This project simulates how a modern data analyst works — but fully automated through an **agentic pipeline**:

- Ingest multiple datasets (CSV / Excel)
- Clean and standardize data
- Validate data quality
- Detect relationships across datasets
- Perform cross-dataset analysis
- Generate statistical + AI insights
- Provide an interactive dashboard for exploration

---

## Architecture

The system is built as a **LangGraph multi-agent pipeline**:
Ingestion → Cleaning → Validation → Schema Drift → Relationships → Analysis → LLM Insights


---

## Agents

### Ingestion Agent
- Reads uploaded files
- Profiles schema (columns, counts, types)
- Initializes pipeline state

### Cleaning Agent
- Standardizes column names
- Removes duplicates
- Outputs cleaned datasets
- Logs transformations

### Validation Agent
- Detects empty datasets
- Flags high missing values
- Produces validation reports
- Controls retry logic in the graph

### Schema Drift Agent
- Compares schemas across files
- Detects structural differences between datasets
- Runs in pipeline (not surfaced in UI)

### Relationship Agent
- Identifies shared columns across datasets
- Suggests optimal join keys
- Executes full joins (not just previews)
- Generates cross-dataset insights (correlation + distribution patterns)

### Analysis Agent
- Computes summary statistics
- Generates charts:
  - Histograms
  - Bar charts
  - Scatter plots
  - Box plots
  - Line charts
  - Correlation heatmaps
- Produces rule-based insights

### LLM Insights Agent
- Uses GPT-4o-mini to generate structured insights
- Returns JSON output with:
  - Summary
  - Key findings
  - Data quality observations
  - Recommended next steps
  - Watch-outs

---

## Features

### Multi-file Analysis
- Upload **1–5 CSV or Excel files**
- Analyze datasets independently and jointly

### Data Quality Reporting
- Missing value detection
- Duplicate removal tracking
- Validation pass/fail status

### Relationship Detection
- Automatic join key detection
- Full dataset joins
- Cross-dataset insights

### Interactive Visualization
- Dynamic chart builder
- Multiple chart types
- AI-suggested visualizations
- Correlation heatmaps

### AI Insights
- LLM-generated structured insights
- Context-aware recommendations
- Dataset-agnostic analysis

### Downloads
- Cleaned datasets
- Validated datasets
- Join previews

---

## Tech Stack

- **Python**
- **LangGraph** (agent orchestration)
- **Streamlit** (frontend UI)
- **Pandas** (data processing)
- **Plotly** (interactive charts)
- **Pydantic** (state management)
- **OpenAI API** (LLM insights)
- **python-dotenv** (env management)

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Ananyaa-Tanwar/multi-agent-data-pipeline.git
cd multi-agent-data-pipeline
```

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Running the App

Start the Streamlit app:

```bash
PYTHONPATH=. streamlit run src/app/streamlit_app.py
```

Open in your browser: http://localhost:8501

Upload 1–5 CSV or Excel files and click **Run analysis**.

---

## Example Use Case

Upload the included sample dataset (US Candy Distributor) or any combination of related CSVs:

- `Candy_Sales.csv` — 10,000+ transaction records with product, customer, and revenue data
- `Candy_Products.csv` — product catalog with factory assignments and pricing
- `Candy_Factories.csv` — factory locations with lat/long coordinates
- `Candy_Targets.csv` — division-level sales targets

The pipeline will automatically:
- Clean and standardize all four files
- Detect `Product ID` and `Division` as shared keys across files
- Execute inner joins and run cross-dataset correlation analysis
- Generate statistical insights per file and across the merged dataset
- Deliver an AI-written summary with specific findings, data quality flags, recommended next steps, and risks to watch

---

## What Was Built

| Capability | Detail |
|---|---|
| Agentic orchestration | Six-node LangGraph pipeline with conditional routing and retry logic on validation failure |
| Data cleaning | Snake_case normalization, duplicate removal, whitespace stripping — fully logged per file |
| Validation | Missing value detection, empty dataset checks, error vs. warning severity levels |
| Relationship detection | Shared column detection across all file pairs, automated inner join execution, cross-dataset analysis |
| Statistical analysis | Per-column summaries, distribution charts, correlation heatmaps, AI-suggested visualizations |
| LLM insights | GPT-4o-mini generates structured findings, data quality observations, next steps, and risk flags |
| LangSmith tracing | Full pipeline observability via environment variable configuration |
| Interactive UI | Streamlit app with dynamic chart builder, downloadable outputs, and one-click sample data loading |

---

## Why This Project Matters

Most data pipelines are either rigid ETL scripts or black-box notebooks. This project demonstrates a third pattern: a **modular, agentic pipeline** where each processing step is an independent agent with a defined input/output contract, orchestrated by a state graph rather than hardcoded control flow.

Practically, this means:
- New agents can be added without touching existing ones
- Conditional routing (retry on validation failure, skip on error) is declarative not imperative
- The same architecture scales from five-file CSV analysis to production data workflows

Built with **LangGraph**, **Streamlit**, **Pandas**, **Plotly**, and the **OpenAI API**.