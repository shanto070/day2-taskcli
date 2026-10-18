"""Persist tasks to a JSON file using pathlib."""

import json
import logging
from pathlib import Path

from taskcli.models import Task

logger = logging.getLogger(__name__)

DEFAULT_PATH = Path.home() / ".taskcli" / "tasks.json"


class StorageError(Exception):
    """The task file could not be read or written."""


class TaskStore:
    def __init__(self, path: Path = DEFAULT_PATH) -> None:
        self.path = path

    def load(self) -> list[Task]:
        if not self.path.exists():
            logger.debug("No task file at %s yet; starting empty", self.path)
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            tasks = [Task.from_dict(item) for item in raw]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise StorageError(f"Could not read {self.path}: {exc}") from exc
        logger.debug("Loaded %d task(s) from %s", len(tasks), self.path)
        return tasks

    def save(self, tasks: list[Task]) -> None:
        payload = json.dumps([task.to_dict() for task in tasks], indent=2)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # Write to a temp file, then rename over the real one, so a crash
            # mid-write never leaves a half-written tasks.json behind.
            tmp_path = self.path.with_suffix(".tmp")
            tmp_path.write_text(payload + "\n", encoding="utf-8")
            tmp_path.replace(self.path)
        except OSError as exc:
            raise StorageError(f"Could not write {self.path}: {exc}") from exc
        logger.debug("Saved %d task(s) to %s", len(tasks), self.path)
