from .model import Recipe, RecipePool


def _recipes_conflict(a: Recipe, b: Recipe) -> bool:
    a_norm = frozenset(x.lower() for x in a.inputs)
    b_norm = frozenset(x.lower() for x in b.inputs)
    return bool(a_norm & b_norm)


def assign_pools(recipes: list[Recipe]) -> list[RecipePool]:
    """Assign recipes to conflict-free pools using the DSatur graph coloring algorithm.

    DSatur is deterministic given consistent tie-breaking and produces near-optimal
    (often optimal) colorings, ensuring the same input always yields the same output.
    """
    if not recipes:
        return []

    n = len(recipes)

    adj: list[set[int]] = [set() for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if _recipes_conflict(recipes[i], recipes[j]):
                adj[i].add(j)
                adj[j].add(i)

    colors = [-1] * n
    degree = [len(adj[i]) for i in range(n)]
    neighbor_colors: list[set[int]] = [set() for _ in range(n)]

    def saturation(i: int) -> int:
        return len(neighbor_colors[i])

    def pick_next() -> int:
        uncolored = [i for i in range(n) if colors[i] == -1]
        # Highest saturation → highest degree → lowest name (alphabetical stability)
        return min(uncolored, key=lambda i: (-saturation(i), -degree[i], recipes[i].name.lower()))

    for _ in range(n):
        v = pick_next()

        used = neighbor_colors[v]
        color = 0
        while color in used:
            color += 1

        colors[v] = color

        for u in adj[v]:
            if colors[u] == -1:
                neighbor_colors[u].add(color)

    num_pools = max(colors) + 1
    pools = [RecipePool(id=i + 1) for i in range(num_pools)]
    for i, color in enumerate(colors):
        pools[color].recipes.append(recipes[i])

    for pool in pools:
        pool.recipes.sort(key=lambda r: r.name.lower())

    return pools
