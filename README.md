# GTNH Utils

A CLI toolkit for GregTech: New Horizons.

## `recipes` — split recipes into conflict-free machine pools

Some machines (e.g. alloy smelters) use a shared input buffer. If two recipes share an ingredient and both are registered to the same machine, crafting them simultaneously can cause the machine to accidentally start the wrong recipe.

**Example:** Tumbaga (Gold + Copper) and Electrum (Gold + Silver) share Gold. If both sit in the same machine pool and you add Gold + Copper + Silver to the buffer, the machine might grab Gold + Silver and produce Electrum instead of Tumbaga.

This command builds a conflict graph — nodes are recipes, edges connect recipes that share at least one ingredient — then applies the **DSatur** graph-colouring algorithm to partition recipes into the minimum number of pools where no two recipes in the same pool share an ingredient.

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
| `FILE` | Path to the input YAML file containing recipes |
| `-o / --output FILE` | Output YAML path (default: `<input>_pools.yaml`) |

### Example

```bash
python tool.py recipes examples/alloy_smelter.yaml
python tool.py recipes examples/alloy_smelter.yaml --output my_pools.yaml
```

Prints a colour-coded table for each pool to the terminal and writes the full assignment to a YAML file.

## Input format

```yaml
recipes:
  - name: Electrum
    inputs: [Gold, Silver]
  - name: Tumbaga
    inputs: [Gold, Copper]
  - name: Blue Alloy
    inputs: [Silver, Electrotine]
  # ...
```

- `name` — human-readable recipe name (case-preserved in all output)
- `inputs` — list of ingredient names (case-insensitive for conflict detection, order does not matter)

## Output format

```yaml
pools:
  - id: 1
    recipes:
      - name: Electrum
        inputs: [Gold, Silver]
  - id: 2
    recipes:
      - name: Tumbaga
        inputs: [Copper, Gold]
      - name: Blue Alloy
        inputs: [Electrotine, Silver]
```

## Algorithm

Conflict detection uses pairwise ingredient-set intersection: recipes A and B conflict iff `inputs(A) ∩ inputs(B) ≠ ∅` (case-insensitive).

Pool assignment uses **DSatur** (Brélaz 1979) — a greedy graph-colouring heuristic that always colours the vertex with the highest *saturation* (number of distinct colours already used by its neighbours) next. Ties are broken first by degree then alphabetically by name, making results fully deterministic. DSatur finds the optimal colouring on many real-world graphs and is significantly better than plain greedy colouring.

## Project layout

```
tool.py                              entry point
gtnh_utils/
  cli.py                             Click-based CLI (top-level commands)
  modes/
    recipes/
      model.py                       Recipe / RecipePool dataclasses
      loader.py                      YAML → Recipe list
      solver.py                      DSatur pool assignment
      formatter.py                   Rich terminal output
      writer.py                      RecipePool list → YAML
examples/
  alloy_smelter.yaml                 sample input
  alloy_smelter_pools.yaml           sample output (generated)
```
