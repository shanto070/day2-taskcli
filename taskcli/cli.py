"""Command-line interface: parse arguments, configure logging, dispatch."""

import argparse
import logging
import sys
from collections import Counter
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TypeAlias

from taskcli import __version__
from taskcli.models import Priority, Status, Task, filter_tasks, next_id
from taskcli.storage import DEFAULT_PATH, StorageError, TaskStore

logger = logging.getLogger(__name__)

# Every sub-command handler has this shape, so the dispatcher can treat them
# all the same way.
Handler: TypeAlias = Callable[[argparse.Namespace, TaskStore], int]


def find_task(tasks: list[Task], task_id: int) -> Task | None:
    return next((task for task in tasks if task.id == task_id), None)


def cmd_add(args: argparse.Namespace, store: TaskStore) -> int:
    tasks = store.load()
    task = Task(id=next_id(tasks), title=args.title, priority=args.priority)
    tasks.append(task)
    store.save(tasks)
    logger.info("Added task %d with priority %s", task.id, task.priority)
    print(f"Added task {task.id}: {task.title} [{task.priority}]")
    return 0


def cmd_list(args: argparse.Namespace, store: TaskStore) -> int:
    tasks = list(filter_tasks(store.load(), status=args.status, priority=args.priority))
    if not tasks:
        print("No tasks found.")
        return 0
    print(f"{'ID':>3}  {'DONE':<4}  {'PRIORITY':<8}  TITLE")
    for task in tasks:
        mark = "x" if task.status is Status.DONE else " "
        print(f"{task.id:>3}  [{mark}]   {task.priority:<8}  {task.title}")
    return 0


def cmd_done(args: argparse.Namespace, store: TaskStore) -> int:
    tasks = store.load()
    task = find_task(tasks, args.id)
    if task is None:
        logger.error("No task with id %d", args.id)
        return 1
    if task.status is Status.DONE:
        logger.warning("Task %d is already done", task.id)
        return 0
    task.mark_done()
    store.save(tasks)
    print(f"Completed task {task.id}: {task.title}")
    return 0


def cmd_delete(args: argparse.Namespace, store: TaskStore) -> int:
    tasks = store.load()
    remaining = [task for task in tasks if task.id != args.id]
    if len(remaining) == len(tasks):
        logger.error("No task with id %d", args.id)
        return 1
    store.save(remaining)
    print(f"Deleted task {args.id}")
    return 0


def cmd_stats(args: argparse.Namespace, store: TaskStore) -> int:
    tasks = store.load()
    by_status = Counter(task.status for task in tasks)
    open_by_priority = Counter(
        task.priority for task in filter_tasks(tasks, status=Status.TODO)
    )
    print(
        f"Total: {len(tasks)}  "
        f"todo: {by_status[Status.TODO]}  done: {by_status[Status.DONE]}"
    )
    print(
        "Open by priority: " + ", ".join(f"{p}={open_by_priority[p]}" for p in Priority)
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="taskcli", description="A tiny task tracker for the terminal."
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="show more logs (-v = info, -vv = debug)",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_PATH,
        help=f"task file to use (default: {DEFAULT_PATH})",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    add = sub.add_parser("add", help="add a new task")
    add.add_argument("title", help="what needs doing")
    add.add_argument(
        "-p",
        "--priority",
        type=Priority,
        choices=list(Priority),
        default=Priority.MEDIUM,
    )
    add.set_defaults(handler=cmd_add)

    list_ = sub.add_parser("list", help="list tasks")
    list_.add_argument("--status", type=Status, choices=list(Status))
    list_.add_argument("--priority", type=Priority, choices=list(Priority))
    list_.set_defaults(handler=cmd_list)

    done = sub.add_parser("done", help="mark a task as done")
    done.add_argument("id", type=int)
    done.set_defaults(handler=cmd_done)

    delete = sub.add_parser("delete", help="delete a task")
    delete.add_argument("id", type=int)
    delete.set_defaults(handler=cmd_delete)

    stats = sub.add_parser("stats", help="show task counts")
    stats.set_defaults(handler=cmd_stats)

    return parser


def configure_logging(verbosity: int) -> None:
    """Send logs to stderr so they never mix with the command's real output."""
    level = {0: logging.WARNING, 1: logging.INFO}.get(verbosity, logging.DEBUG)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(args.verbose)
    store = TaskStore(args.file)
    logger.debug("Running %r with task file %s", args.command, store.path)
    handler: Handler = args.handler
    try:
        return handler(args, store)
    except StorageError as exc:
        logger.error("%s", exc)
        return 1
