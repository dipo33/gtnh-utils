from .model import Recipe, RecipePool


def _norm(recipe: Recipe) -> frozenset[str]:
    return frozenset(x.lower() for x in recipe.inputs)


def _pool_is_valid(pool: list[Recipe], rest: list[Recipe]) -> bool:
    """A pool is valid when both conditions hold:

    Internal — every pool recipe has at least one ingredient that appears in no
    other pool recipe.  If every ingredient of recipe R appears somewhere else in
    the pool, crafting the others simultaneously provides all inputs needed to
    accidentally trigger R.

    External — no rest recipe's inputs are fully covered by the combined inputs
    of all pool recipes.  The machine knows all recipes; if the pool's ingredient
    footprint satisfies a rest recipe, it will be accidentally crafted.
    """
    if not pool:
        return True

    normed = [_norm(r) for r in pool]
    pool_union = frozenset().union(*normed)

    for i, ing in enumerate(normed):
        others_union = frozenset().union(*(normed[j] for j in range(len(pool)) if j != i))
        if ing <= others_union:
            return False

    for r in rest:
        if _norm(r) <= pool_union:
            return False

    return True


def assign_pools(recipes: list[Recipe], rest: list[Recipe] | None = None) -> list[RecipePool]:
    """Assign recipes to the minimum number of conflict-free pools.

    rest recipes are never assigned to a pool but participate in both the
    validity check (external collision) and the difficulty ordering (ingredient
    frequencies across all known recipes, including rest).
    """
    if not recipes:
        return []

    if rest is None:
        rest = []

    freq: dict[str, int] = {}
    for r in recipes + rest:
        for ing in _norm(r):
            freq[ing] = freq.get(ing, 0) + 1

    def difficulty(r: Recipe) -> int:
        return min(freq[ing] for ing in _norm(r))

    ordered = sorted(recipes, key=lambda r: (-difficulty(r), r.name.lower()))

    pools: list[list[Recipe]] = []

    for recipe in ordered:
        for pool in pools:
            if _pool_is_valid(pool + [recipe], rest):
                pool.append(recipe)
                break
        else:
            pools.append([recipe])

    result = []
    for i, pool in enumerate(pools):
        pool.sort(key=lambda r: r.name.lower())
        result.append(RecipePool(id=i + 1, recipes=pool))

    return result
