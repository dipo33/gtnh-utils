from .model import Recipe, RecipePool


def _n(ingredients: frozenset[str]) -> frozenset[str]:
    return frozenset(x.lower() for x in ingredients)


def _pool_is_valid(pool: list[Recipe], rest: list[Recipe]) -> bool:
    """A pool is valid when both conditions hold:

    Internal — every pool recipe R must have at least one consumable ingredient
    not present in (other pool recipes' consumable inputs ∪ all pool non-consumables).
    Non-consumables are permanently in the buffer, so they can satisfy any recipe's
    consumable requirements just as much as active crafting inputs can.

    External — no rest recipe's full input set (consumable + non-consumable) may be
    covered by the pool's total ingredient footprint (all_inputs union).
    """
    if not pool:
        return True

    # Non-consumables from all pool recipes are always in the buffer.
    always_present = frozenset().union(*(_n(r.non_consumable) for r in pool))

    cons = [_n(r.inputs) for r in pool]
    pool_all_union = frozenset().union(*(_n(r.all_inputs) for r in pool))

    # Internal check
    for i in range(len(pool)):
        others_cons_union = frozenset().union(*(cons[j] for j in range(len(pool)) if j != i))
        if cons[i] <= always_present | others_cons_union:
            return False

    # External check
    for r in rest:
        if _n(r.all_inputs) <= pool_all_union:
            return False

    return True


def assign_pools(recipes: list[Recipe], rest: list[Recipe] | None = None) -> list[RecipePool]:
    """Assign recipes to the minimum number of conflict-free pools.

    rest recipes participate in the external validity check and in the
    difficulty ordering but are never assigned to a pool.
    """
    if not recipes:
        return []

    if rest is None:
        rest = []

    freq: dict[str, int] = {}
    for r in recipes + rest:
        for ing in _n(r.all_inputs):
            freq[ing] = freq.get(ing, 0) + 1

    def difficulty(r: Recipe) -> int:
        return min(freq[ing] for ing in _n(r.all_inputs)) if r.all_inputs else 0

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
