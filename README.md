# Multi-Agent Data Analyst (LangGraph + Streamlit)

An end-to-end **multi-agent data analysis system** that ingests multiple datasets, performs automated cleaning and validation, detects relationships across files, and generates interactive visual insights.

Built using **LangGraph for orchestration** and **Streamlit for an interactive UI**.

---

## Overview

This project simulates how a data analyst would approach messy data, but automated through a **multi-agent pipeline**:

- Ingest multiple files (CSV / Excel)
- Clean and standardize datasets
- Validate data quality
- Detect relationships across datasets
- Generate statistical insights and charts
- Provide an interactive dashboard for exploration

---

## Architecture

The system is built as a **LangGraph pipeline** with modular agents:


### Agents

- **Ingestion Agent**
  - Reads uploaded files
  - Profiles schema (columns, types, counts)

- **Cleaning Agent**
  - Standardizes column names
  - Removes duplicates
  - Outputs cleaned datasets

- **Validation Agent**
  - Checks for empty datasets
  - Flags high missing values
  - Produces validation report

- **Relationship Agent**
  - Detects shared columns across files
  - Suggests join keys
  - Generates join previews

- **Analysis Agent**
  - Computes summary statistics
  - Generates charts (histograms, bar charts, correlation heatmaps)
  - Produces human-readable insights

---

## Features

### Multi-file Analysis
- Upload **1–5 CSV or Excel files**
- Each file processed independently and jointly

### Data Quality Reporting
- Missing value detection
- Duplicate removal tracking
- Validation pass/fail status

### Relationship Detection
- Identifies shared columns across datasets
- Suggests join keys
- Generates join previews

### Interactive Visualization
- Histogram, bar chart, scatter, box plot, line chart
- Correlation heatmaps (when applicable)
- Dynamic chart builder (user selects columns and chart types)

### Insights Generation
- Summary statistics
- Key column-level insights
- Relationship insights between datasets

### Downloads
- Cleaned datasets
- Validated datasets
- Join previews

---

## Tech Stack

- **Python**
- **LangGraph** (multi-agent orchestration)
- **Streamlit** (frontend UI)
- **Pandas** (data processing)
- **Plotly** (interactive visualizations)
- **Pydantic** (structured state management)

---

## Installation

Clone the repository:
```bash
git clone https://github.com/your-username/multi-agent-data-pipeline.git
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

Upload:
- `orders.csv`
- `customers.csv`

The system will:
- Detect `customer_id` as a shared key
- Suggest a join between datasets
- Generate insights such as:
  - Order distribution
  - Customer frequency
  - Relationships between numeric variables

---

## Project Structure
src/
├── agents/
│   ├── ingestion.py
│   ├── cleaner.py
│   ├── validator.py
│   ├── relationship.py
│   └── analyst.py
├── core/
│   ├── state.py
│   ├── artifacts.py
│   └── file_utils.py
├── graph/
│   └── pipeline_graph.py
├── app/
│   └── streamlit_app.py
└── cli/
└── run_pipeline.py

---

## Future Improvements

- [ ] LLM-powered insights (natural language summaries)
- [ ] Automated join execution + cross-dataset analysis
- [ ] Advanced validation rules (schema + constraints)
- [ ] Time-series detection and forecasting
- [ ] Data lineage visualization
- [ ] LangSmith tracing integration

---

## Why This Project Matters

This project demonstrates:

- Building agentic workflows using **LangGraph**
- Combining deterministic data processing with modular agents
- Designing interactive data applications
- Structuring code for scalability and extensibility
