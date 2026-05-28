from pathlib import Path

import yaml

from .model import RecipePool


def write_pools(pools: list[RecipePool], path: Path) -> None:
    data = {
        "pools": [
            {
                "id": pool.id,
                "recipes": [_recipe_dict(recipe) for recipe in pool.recipes],
            }
            for pool in pools
        ]
    }

    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def _recipe_dict(recipe) -> dict:
    d: dict = {
        "name": recipe.name,
        "inputs": sorted(recipe.inputs, key=str.lower),
    }
    if recipe.non_consumable:
        d["non_consumable"] = sorted(recipe.non_consumable, key=str.lower)
    return d
