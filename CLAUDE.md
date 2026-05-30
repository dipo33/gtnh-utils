# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

Python 3.11 via pyenv (`.python-version` pins the version). Always use `.venv` for all commands:

```bash
source .venv/bin/activate   # or prefix commands with .venv/bin/python
.venv/bin/python tool.py recipes inputs/recipes/alloy_smelter.yaml
```

Run the test suite with:

```bash
.venv/bin/pytest tests/ -v
.venv/bin/pytest tests/test_solver.py -v   # solver only
```

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

- **`model.py`** — `Recipe(name, inputs: frozenset[str], non_consumable: frozenset[str])` and `RecipePool(id, recipes)`. `inputs` = consumable ingredients; `non_consumable` = ingredients required but not consumed (always present in pool buffer). `all_inputs` property = union of both. Original casing is preserved; normalization to lowercase is done only inside `solver.py`.
- **`loader.py`** — Parses the input YAML, preserves ingredient casing, returns a `RecipeData(recipes, rest)` named tuple; both lists are sorted alphabetically for downstream determinism.
- **`solver.py`** — Greedy pool assignment. `assign_pools(recipes, rest)` takes both lists; `rest` participates in the validity check and in the ingredient-frequency ordering but is never assigned to a pool. Recipes are ordered hardest-to-place first (`min(ingredient_freq across recipes+rest)` descending, then alphabetically), then greedily assigned to the first valid pool.
- **`formatter.py`** — Rich terminal output; cycles through `_POOL_COLORS`.
- **`writer.py`** — Dumps `RecipePool` list to YAML, ingredients sorted case-insensitively.

### Collision rule (important invariant)

The machine globally knows all recipes. A pool is **invalid** if either:

- *(Internal)* any pool recipe R has every **consumable** ingredient covered by `(other pool recipes' consumable inputs) ∪ (all pool non-consumables)` — non-consumables are permanently in the buffer so they count toward covering.
- *(External)* any `rest` recipe R has every ingredient covered by the full pool union (`all_inputs` of all pool recipes) — the pool's combined ingredient footprint would accidentally trigger R.

Shared ingredients alone are **not** a conflict. Two recipes sharing Copper is fine; the problem is only when a recipe's *entire* input set is covered.

## Adding a new mode

1. Create `gtnh_utils/modes/<name>/` with `__init__.py`.
2. Add a `@cli.command("<name>")` function in `gtnh_utils/cli.py` with lazy imports (see `recipes_cmd` for the pattern).
