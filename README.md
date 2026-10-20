# branch-report

Audit git branches: find stale, merged, and divergent branches and get safe cleanup suggestions. Ships as a CLI and a small importable library, with config files and a plugin hook system.

## Features

- List local (and optionally remote) branches with last commit date, author, and merged status.
- Detect stale branches (no commits in N days, configurable).
- Detect branches already merged into the base branch.
- Suggest cleanup commands (dry-run by default; `--execute` to apply).
- Protected branch patterns (never suggest deleting `main`, `release/*`, ...).
- Multiple output formats: table, JSON, CSV.
- Config file (`.branchreportrc.json`) plus environment/CLI overrides.
- Plugin system: drop Python files into a directory to add custom classifiers.
- Zero runtime dependencies (standard library only).

## Install

```bash
pip install -e .
# with dev deps
pip install -e '.[dev]'
```

## Usage

```bash
# List all branches
branch-report list

# Find stale branches (default 30 days)
branch-report stale --days 14

# Find merged branches
branch-report merged --base develop

# Suggest cleanup (dry run)
branch-report cleanup

# Actually delete
branch-report cleanup --execute --force

# JSON output
branch-report list --format json

# Init config
branch-report config init
```

## Architecture

```
src/branch_report/
  cli.py        # argparse entry point and subcommands
  git.py        # GitRunner: subprocess wrapper around git
  analysis.py   # pure functions: classify, age, protected, suggestions
  config.py     # Config dataclass + load/save/search
  output.py     # table/json/csv renderers
  plugins.py    # plugin loader and application
```

`analysis.py` is kept free of I/O so it is fully unit-testable. `GitRunner` accepts an injectable runner for testing.

## License

MIT
