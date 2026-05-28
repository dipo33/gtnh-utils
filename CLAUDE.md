# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

Python 3.11 via pyenv (`.python-version` pins the version). Always use `.venv` for all commands:

```bash
source .venv/bin/activate   # or prefix commands with .venv/bin/python
.venv/bin/python tool.py recipes examples/alloy_smelter.yaml
```

No test suite or linter is configured yet.

## Running the tool

```bash
.venv/bin/python tool.py recipes FILE [-o OUTPUT]
```

Output defaults to `<input>_pools.yaml` alongside the input file.

## Architecture

The entry point `tool.py` imports `gtnh_utils.cli:cli` (a Click group). Each subcommand maps to a **mode** — a self-contained package under `gtnh_utils/modes/`. Currently only `modes/recipes/` exists; new modes are added by creating a new package there and registering a `@cli.command` in `gtnh_utils/cli.py`.

### `modes/recipes/` pipeline

```
loader.py  →  solver.py  →  formatter.py  (terminal)
                         →  writer.py     (YAML file)
```

- **`model.py`** — `Recipe(name, inputs: frozenset[str])` and `RecipePool(id, recipes)`. `inputs` preserves original casing from the YAML; normalization to lowercase is done only inside `solver.py`.
- **`loader.py`** — Parses the input YAML, preserves ingredient casing, returns recipes sorted alphabetically (for downstream determinism).
- **`solver.py`** — Greedy pool assignment. A pool is **valid** when every recipe has at least one ingredient that appears in no other recipe in the same pool (if all ingredients are covered by others, those others could inadvertently trigger it). Recipes are ordered hardest-to-place first (`min(ingredient_freq)` descending, then alphabetically), then greedily assigned to the first valid pool.
- **`formatter.py`** — Rich terminal output; cycles through `_POOL_COLORS`.
- **`writer.py`** — Dumps `RecipePool` list to YAML, ingredients sorted case-insensitively.

### Collision rule (important invariant)

A recipe C is **unsafe** in a pool when every ingredient of C also appears in at least one *other* recipe in that pool — meaning someone crafting all the others simultaneously inadvertently supplies all inputs needed to trigger C. Shared ingredients alone are **not** a conflict; the check is holistic per recipe against the union of all others in the same pool.

## Adding a new mode

1. Create `gtnh_utils/modes/<name>/` with `__init__.py`.
2. Add a `@cli.command("<name>")` function in `gtnh_utils/cli.py` with lazy imports (see `recipes_cmd` for the pattern).
