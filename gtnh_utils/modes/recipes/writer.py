from pathlib import Path

import yaml

from .model import Recipe, SolverResult


def write_pools(result: SolverResult, path: Path) -> None:
    data: dict = {}

    if result.global_fluids:
        data["global_tanks"] = {
            "fluids": sorted(result.global_fluids, key=str.lower)
        }

    data["pools"] = [_pool_dict(pool, result.bound_fluids) for pool in result.pools]

    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def _pool_dict(pool, bound_fluids: dict) -> dict:
    d: dict = {"id": pool.id}
    pool_bound = bound_fluids.get(pool.id)
    if pool_bound:
        d["bound_tanks"] = {"fluids": sorted(pool_bound, key=str.lower)}
    d["recipes"] = [_recipe_dict(r) for r in pool.recipes]
    return d


def _recipe_dict(recipe: Recipe) -> dict:
    d: dict = {
        "name": recipe.name,
        "inputs": sorted(recipe.inputs, key=str.lower),
    }
    if recipe.non_consumable:
        d["non_consumable"] = sorted(recipe.non_consumable, key=str.lower)
    if recipe.fluid_inputs:
        d["fluid_inputs"] = sorted(recipe.fluid_inputs, key=str.lower)
    return d
