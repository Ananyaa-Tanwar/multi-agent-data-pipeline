from __future__ import annotations

import argparse
from pathlib import Path

from src.core.artifacts import init_state, write_json
from src.graph.pipeline_graph import build_graph


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", required=True)
    args = parser.parse_args()

    input_paths = [Path(p) for p in args.inputs]

    for path in input_paths:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

    state = init_state(input_paths=input_paths)

    graph = build_graph()
    final_state = graph.invoke(state)

    if isinstance(final_state, dict):
        final_state_dict = final_state
    else:
        final_state_dict = final_state.model_dump()

    report_path = Path(final_state_dict["run_dir"]) / "reports" / "final_state.json"
    write_json(report_path, final_state_dict)

    print("Pipeline complete.")
    print("Run directory:", final_state_dict["run_dir"])
    print("Status:", final_state_dict["status"])
    print("Final state report:", report_path)


if __name__ == "__main__":
    main()