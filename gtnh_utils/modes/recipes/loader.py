from pathlib import Path
from typing import NamedTuple

import yaml

from .model import Recipe


class RecipeData(NamedTuple):
    recipes: list[Recipe]
    rest: list[Recipe]


def _parse(items: list[dict]) -> list[Recipe]:
    return sorted(
        [
            Recipe(
                name=item["name"],
                inputs=frozenset(str(inp) for inp in item.get("inputs", [])),
                non_consumable=frozenset(str(inp) for inp in item.get("non_consumable", [])),
                fluid_inputs=frozenset(str(inp) for inp in item.get("fluid_inputs", [])),
            )
            for item in items
        ],
        key=lambda r: r.name.lower(),
    )


def load_recipes(path: Path) -> RecipeData:
    with open(path) as f:
        data = yaml.safe_load(f)

    return RecipeData(
        recipes=_parse(data.get("recipes", [])),
        rest=_parse(data.get("rest", [])),
    )
