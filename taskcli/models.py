"""Domain models: what a task *is*, independent of storage or the CLI."""

from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Self


class Priority(StrEnum):
    """StrEnum members are real strings, so they serialize to JSON as-is."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Status(StrEnum):
    TODO = "todo"
    DONE = "done"


@dataclass(slots=True)
class Task:
    id: int
    title: str
    priority: Priority = Priority.MEDIUM
    status: Status = Status.TODO
    # default_factory runs per instance; a plain `= datetime.now()` would be
    # evaluated once at import time and shared by every task.
    created_at: datetime = field(default_factory=datetime.now)

    def mark_done(self) -> None:
        self.status = Status.DONE

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat(timespec="seconds")
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            id=int(data["id"]),
            title=str(data["title"]),
            priority=Priority(data["priority"]),
            status=Status(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
        )


def filter_tasks(
    tasks: Iterable[Task],
    status: Status | None = None,
    priority: Priority | None = None,
) -> Iterator[Task]:
    """Lazily yield tasks matching the filters (a generator, not a list)."""
    for task in tasks:
        if status is not None and task.status != status:
            continue
        if priority is not None and task.priority != priority:
            continue
        yield task


def next_id(tasks: Iterable[Task]) -> int:
    return max((task.id for task in tasks), default=0) + 1
