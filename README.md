# taskcli — Day 2 Assignment

A small task-tracker CLI written for **Day 2: Python for Backend Engineers**.

It uses `argparse`, full type hints, `dataclasses`, `enum`, `pathlib`, `logging`
and a generator. It passes `ruff check`, `ruff format --check` and `mypy --strict`.

## Setup

Requires Python 3.11+.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -e ".[dev]"
```

## Usage

```bash
taskcli add "Read the typing docs" --priority high
taskcli add "Watch the generators video"
taskcli list
taskcli list --status todo
taskcli done 1
taskcli delete 2
taskcli stats
taskcli -v add "Show info logs"     # -v = INFO logs, -vv = DEBUG logs
taskcli --file my-tasks.json list   # use a different task file
taskcli --help
```

Global options (`-v`, `--file`) go **before** the command name.
You can also run it without installing: `python -m taskcli list`.

Tasks are saved to `~/.taskcli/tasks.json` by default.

Example:

```text
$ taskcli list
 ID  DONE  PRIORITY  TITLE
  1  [x]   high      Read the typing docs
  2  [ ]   medium    Watch ArjanCodes type hints video
```

## Code quality

```bash
ruff check .            # lint
ruff format --check .   # formatting
mypy taskcli            # static type check (strict mode)
```

All three pass. Ruff's rules are in `pyproject.toml`. They include `ANN`, so
ruff fails if any function is missing type hints.

## Where each Day 2 topic is used

| Topic | Where |
| --- | --- |
| Type hints | Every function; `Self`, `X \| None`, `Iterator`, a `TypeAlias` for `Handler` |
| Dataclasses | `Task` in `models.py` (`slots=True`, `field(default_factory=...)`) |
| Enums | `Priority` and `Status` (`StrEnum`) in `models.py` |
| pathlib | `storage.py`: `Path.home()`, `mkdir(parents=True)`, `read_text`, safe write via temp file + `replace` |
| Logging | Module loggers via `logging.getLogger(__name__)`; level set by `-v`; logs go to stderr, output to stdout |
| Generators | `filter_tasks()` in `models.py` yields matches lazily |
| Virtual env + packaging | `.venv`, `pyproject.toml`, `pip install -e ".[dev]"`, `taskcli` console script |
| Ruff | `[tool.ruff]` config in `pyproject.toml` |

## Project layout

```text
day2-taskcli/
├── pyproject.toml      # metadata, dependencies, entry point, ruff + mypy config
├── README.md
└── taskcli/
    ├── __init__.py     # package version
    ├── __main__.py     # enables `python -m taskcli`
    ├── cli.py          # argparse, logging setup, command handlers
    ├── models.py       # Task dataclass, enums, filter generator
    └── storage.py      # JSON persistence with pathlib
```
