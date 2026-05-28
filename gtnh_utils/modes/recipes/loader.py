from pathlib import Path

import yaml

from .model import Recipe


def load_recipes(path: Path) -> list[Recipe]:
    with open(path) as f:
        data = yaml.safe_load(f)

    recipes = []
    for item in data.get("recipes", []):
        recipes.append(
            Recipe(
                name=item["name"],
                inputs=frozenset(str(inp) for inp in item["inputs"]),
            )
        )

    return sorted(recipes, key=lambda r: r.name.lower())
