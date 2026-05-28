from .model import Recipe, RecipePool


def _norm(recipe: Recipe) -> frozenset[str]:
    return frozenset(x.lower() for x in recipe.inputs)


def _pool_is_valid(pool: list[Recipe]) -> bool:
    """A pool is valid when every recipe has at least one ingredient that appears
    in no other recipe in the pool.  If all of a recipe's ingredients are
    collectively present across the other recipes, someone crafting those others
    simultaneously would accidentally provide enough inputs to also trigger it.
    """
    if len(pool) <= 1:
        return True

    normed = [_norm(r) for r in pool]

    for i, recipe_inputs in enumerate(normed):
        others_union = frozenset().union(*(normed[j] for j in range(len(pool)) if j != i))
        if recipe_inputs <= others_union:
            return False

    return True


def assign_pools(recipes: list[Recipe]) -> list[RecipePool]:
    """Assign recipes to conflict-free pools using a greedy heuristic.

    Ordering heuristic: recipes whose ingredients are all "popular" (each one
    appearing in many other recipes) are the hardest to place without causing
    a conflict, so they are scheduled first.  Within the same difficulty band,
    recipes are ordered alphabetically so the result is fully deterministic.
    """
    if not recipes:
        return []

    freq: dict[str, int] = {}
    for recipe in recipes:
        for ing in _norm(recipe):
            freq[ing] = freq.get(ing, 0) + 1

    def difficulty(recipe: Recipe) -> int:
        return min(freq[ing] for ing in _norm(recipe))

    ordered = sorted(recipes, key=lambda r: (-difficulty(r), r.name.lower()))

    pools: list[list[Recipe]] = []

    for recipe in ordered:
        for pool in pools:
            if _pool_is_valid(pool + [recipe]):
                pool.append(recipe)
                break
        else:
            pools.append([recipe])

    result = []
    for i, pool in enumerate(pools):
        pool.sort(key=lambda r: r.name.lower())
        result.append(RecipePool(id=i + 1, recipes=pool))

    return result
