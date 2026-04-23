from __future__ import annotations

import json
import shutil
import secrets
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from src.core.state import PipelineState


def create_run_dir(base_dir: Path = Path("runs")) -> tuple[str, Path]:
    base_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = secrets.token_hex(3)
    run_id = f"{timestamp}_{short_id}"
    run_dir = base_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "raw").mkdir(exist_ok=True)
    (run_dir / "cleaned").mkdir(exist_ok=True)
    (run_dir / "validated").mkdir(exist_ok=True)
    (run_dir / "reports").mkdir(exist_ok=True)
    (run_dir / "charts").mkdir(exist_ok=True)

    return run_id, run_dir


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)


def init_state(input_paths: List[Path], max_retries: int = 1) -> PipelineState:
    run_id, run_dir = create_run_dir()

    copied_paths = []
    for path in input_paths:
        dest = run_dir / "raw" / path.name
        shutil.copy(path, dest)
        copied_paths.append(dest)

    return PipelineState(
        run_id=run_id,
        run_dir=run_dir,
        input_paths=copied_paths,
        max_retries=max_retries,
        status="running",
    )