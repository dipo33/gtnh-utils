from .model import Recipe, RecipePool, SolverResult


def _n(ingredients: frozenset[str]) -> frozenset[str]:
    return frozenset(x.lower() for x in ingredients)


def _pool_is_valid(
    pool: list[Recipe],
    rest: list[Recipe],
    global_fluids: frozenset[str] = frozenset(),
    bound_fluids_for_pool: frozenset[str] = frozenset(),
) -> bool:
    """A pool is valid when both conditions hold:

    Internal — every pool recipe R must have at least one consumable ingredient
    (solid or bound fluid) not covered by (other recipes' consumable ingredients ∪
    always_present). always_present = pool non-consumables ∪ global fluids.

    External — no rest recipe's full input set may be covered by the pool's
    total footprint (always_present ∪ all consumable ingredients in the pool).
    """
    if not pool:
        return True

    always_present = frozenset().union(*(_n(r.non_consumable) for r in pool)) | global_fluids

    def recipe_cons(r: Recipe) -> frozenset[str]:
        return _n(r.inputs) | (_n(r.fluid_inputs) & bound_fluids_for_pool)

    cons = [recipe_cons(r) for r in pool]
    pool_footprint = always_present | frozenset().union(*cons)

    if len(pool) > 1:
        for i in range(len(pool)):
            others_cons_union = frozenset().union(*(cons[j] for j in range(len(pool)) if j != i))
            if cons[i] <= always_present | others_cons_union:
                return False

    for r in rest:
        if _n(r.all_inputs) <= pool_footprint:
            return False

    return True


def _promote_fluids(
    pools: list[RecipePool],
    rest: list[Recipe],
) -> tuple[frozenset[str], dict[int, frozenset[str]]]:
    """Phase 2: greedily promote each bound fluid to global where safe.

    Returns (global_fluids_lower, bound_by_pool_lower) both in lowercase.
    """
    pool_fluids = {
        pool.id: frozenset().union(*(_n(r.fluid_inputs) for r in pool.recipes))
        for pool in pools
    }
    all_fluids = frozenset().union(*pool_fluids.values())
    global_fluids: set[str] = set()

    for f in sorted(all_fluids):
        candidate_gf = frozenset(global_fluids | {f})
        if all(
            _pool_is_valid(
                pool.recipes, rest, candidate_gf, pool_fluids[pool.id] - candidate_gf
            )
            for pool in pools
        ):
            global_fluids.add(f)

    bound_by_pool = {
        pool.id: pool_fluids[pool.id] - global_fluids
        for pool in pools
        if pool_fluids[pool.id] - global_fluids
    }
    return frozenset(global_fluids), bound_by_pool


def assign_pools(recipes: list[Recipe], rest: list[Recipe] | None = None) -> SolverResult:
    """Assign recipes to the minimum number of conflict-free pools.

    Two-phase approach:
      Phase 1 — greedy pool assignment treating all fluids as bound consumables.
                Fluids act as full differentiating ingredients, giving the solver
                the best chance to pack recipes together.
      Phase 2 — for each fluid, try promoting it from bound to global (shared tank).
                A fluid is promoted only if doing so leaves every pool valid.
                Prefer global to minimise the number of bound tanks.

    rest recipes participate in validity checks and difficulty ordering but are
    never assigned to a pool.
    """
    if not recipes:
        return SolverResult([], frozenset(), {})

    if rest is None:
        rest = []

    casing: dict[str, str] = {}
    for r in recipes + rest:
        for f in r.fluid_inputs:
            casing.setdefault(f.lower(), f)

    freq: dict[str, int] = {}
    for r in recipes + rest:
        for ing in _n(r.all_inputs):
            freq[ing] = freq.get(ing, 0) + 1

    def difficulty(r: Recipe) -> int:
        return min(freq[ing] for ing in _n(r.all_inputs)) if r.all_inputs else 0

    ordered = sorted(recipes, key=lambda r: (-difficulty(r), r.name.lower()))

    # Phase 1: pool assignment — all fluids treated as bound consumables.
    pools: list[list[Recipe]] = []
    for recipe in ordered:
        for pool in pools:
            all_fluids = frozenset().union(*(_n(r.fluid_inputs) for r in pool + [recipe]))
            if _pool_is_valid(pool + [recipe], rest, frozenset(), all_fluids):
                pool.append(recipe)
                break
        else:
            pools.append([recipe])

    result_pools = []
    for i, pool in enumerate(pools):
        pool.sort(key=lambda r: r.name.lower())
        result_pools.append(RecipePool(id=i + 1, recipes=pool))

    # Phase 2: promote fluids to global where safe.
    global_lower, bound_lower = _promote_fluids(result_pools, rest)

    return SolverResult(
        result_pools,
        frozenset(casing.get(f, f) for f in global_lower),
        {pid: frozenset(casing.get(f, f) for f in fluids) for pid, fluids in bound_lower.items()},
    )
