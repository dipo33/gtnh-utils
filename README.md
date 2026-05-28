# GTNH Utils

A CLI toolkit for GregTech: New Horizons.

## `recipes` — split recipes into conflict-free machine pools

Machines with a shared input buffer (e.g. alloy smelters) globally know all recipes. When you pipe in ingredients for multiple recipes simultaneously, the machine can accidentally trigger an unintended recipe if its inputs happen to be a subset of what's in the buffer.

**Example:** crafting Tumbaga (Gold+Copper) and Blue Alloy (Silver+Electrotine) together puts Gold, Copper, Silver, and Electrotine in the buffer. If Electrum (Gold+Silver) is a recipe the machine knows, it will be accidentally triggered — even if you never intended to automate Electrum here.

This command assigns recipes to the minimum number of pools (one pool = one machine) so that no pool's combined ingredient footprint can accidentally satisfy any other known recipe.

The output is deterministic: identical input always produces identical pool assignments.

## Requirements

- Python 3.11+
- [pyenv](https://github.com/pyenv/pyenv) (recommended)

## Setup

```bash
git clone <repo-url>
cd gt-recipe-pools

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

## Usage

```
python tool.py recipes FILE [OPTIONS]
```

| Argument / Option | Description |
|---|---|
| `FILE` | Path to the input YAML file |
| `-o / --output FILE` | Output YAML path (default: `<input>_pools.yaml`) |

```bash
python tool.py recipes examples/alloy_smelter.yaml
python tool.py recipes examples/alloy_smelter.yaml --output my_pools.yaml
```

## Input format

```yaml
recipes:
  - name: Tumbaga
    inputs: [Gold, Copper]
  - name: Blue Alloy
    inputs: [Silver, Electrotine]
  # ...

rest:                          # optional
  - name: Electrum
    inputs: [Gold, Silver]
  # ...
```

**`recipes`** — recipes you want to automate; these are assigned to pools.

**`rest`** — other recipes this machine type knows about that you are *not* automating. Optional, but important for correctness: if a recipe exists in the game and the machine knows it, omitting it from `rest` means the tool won't detect accidental crafting of that recipe. You can omit entries you're certain won't cause conflicts.

- `name` — human-readable (case-preserved in all output)
- `inputs` — ingredient names (case-insensitive for conflict detection, order does not matter)

## Output format

Only pools from the `recipes` section appear in the output. `rest` entries are never emitted.

```yaml
pools:
  - id: 1
    recipes:
      - name: Blue Alloy
        inputs: [Electrotine, Silver]
  - id: 2
    recipes:
      - name: Tumbaga
        inputs: [Copper, Gold]
```

## Algorithm

**Collision rule:** a recipe R is unsafe in a pool when:
- *(internal)* every ingredient of R also appears in at least one other recipe in the same pool — crafting the others simultaneously supplies all inputs needed to accidentally trigger R; or
- *(external)* every ingredient of R (a `rest` recipe) is covered by the pool's combined ingredient footprint.

Note: two recipes *sharing* an ingredient is not itself a conflict. What matters is whether any recipe's full input set is covered.

**Assignment:** greedy, hardest-to-place first. Difficulty = `min(frequency of each ingredient across all known recipes)`. Ties broken alphabetically for full determinism.

## Project layout

```
tool.py                              entry point
gtnh_utils/
  cli.py                             Click-based CLI (top-level commands)
  modes/
    recipes/
      model.py                       Recipe / RecipePool dataclasses
      loader.py                      YAML → RecipeData(recipes, rest)
      solver.py                      greedy pool assignment
      formatter.py                   Rich terminal output
      writer.py                      RecipePool list → YAML
examples/
  alloy_smelter.yaml                 sample input
  alloy_smelter_pools.yaml           sample output (generated)
```
