from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path

from book_translator.models.job import JobMeta

RUNS_BASE: Path = Path.home() / ".local" / "share" / "book-translator" / "runs"

# Run state constants (D-21)
STATE_RUNNING = "running"
STATE_FAILED = "failed"
STATE_COMPLETED = "completed"
STATE_UNKNOWN = "unknown"

TERMINAL_STATES = {STATE_FAILED, STATE_COMPLETED}


class JobStore:
    """File-system backed job store. Each run is a directory under ``base``."""

    def __init__(self, base: Path = RUNS_BASE) -> None:
        self.base = base
        self.base.mkdir(parents=True, exist_ok=True)

    def create_run(self, meta: JobMeta) -> str:
        """Create a new run directory, write meta.json, return 12-char run ID."""
        run_id = uuid.uuid4().hex[:12]
        run_dir = self.base / run_id
        (run_dir / "src").mkdir(parents=True)
        (run_dir / "dst").mkdir(parents=True)
        self._write_meta(run_dir, meta)
        return run_id

    def _write_meta(self, run_dir: Path, meta: JobMeta) -> None:
        """Write meta.json atomically via tmp → os.replace."""
        tmp = run_dir / "meta.json.tmp"
        tmp.write_text(
            json.dumps({"model": meta.model, "params": meta.params}, indent=2),
            encoding="utf-8",
        )
        os.replace(tmp, run_dir / "meta.json")

    def read_meta(self, run_id: str) -> JobMeta:
        """Read meta.json and return a JobMeta instance."""
        data = json.loads((self.base / run_id / "meta.json").read_text("utf-8"))
        return JobMeta(model=data["model"], params=data.get("params", {}))

    def update_meta(self, run_id: str, meta: JobMeta) -> None:
        """Overwrite meta.json for an existing run (atomic)."""
        self._write_meta(self.run_dir(run_id), meta)

    def list_runs(self) -> list[str]:
        """Return sorted list of all run IDs."""
        return sorted(p.name for p in self.base.iterdir() if p.is_dir())

    def run_dir(self, run_id: str) -> Path:
        """Return the root directory for a run."""
        return self.base / run_id

    def src_dir(self, run_id: str) -> Path:
        """Return the src/ subdirectory for a run."""
        return self.run_dir(run_id) / "src"

    def dst_dir(self, run_id: str) -> Path:
        """Return the dst/ subdirectory for a run."""
        return self.run_dir(run_id) / "dst"

    def delete_run(self, run_id: str) -> None:
        """Remove a run directory and all its contents."""
        shutil.rmtree(self.run_dir(run_id))

    def list_run_metas(self) -> list[tuple[str, JobMeta]]:
        """Return (run_id, JobMeta) pairs for all existing runs, sorted by run_id."""
        result = []
        for run_id in self.list_runs():
            try:
                meta = self.read_meta(run_id)
            except Exception:
                meta = JobMeta(model="unknown", params={"state": "unknown"})
            result.append((run_id, meta))
        return result
