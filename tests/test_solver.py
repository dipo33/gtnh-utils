"""
Tests for the pool assignment solver.

Naming convention for recipe helpers: r(name, consumable_inputs, non_consumable_inputs=())
"""
import pytest
from gtnh_utils.modes.recipes.model import Recipe
from gtnh_utils.modes.recipes.solver import assign_pools, _pool_is_valid


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def r(name: str, inputs, non_consumable=()) -> Recipe:
    return Recipe(name, frozenset(inputs), frozenset(non_consumable))


# ---------------------------------------------------------------------------
# _pool_is_valid
# ---------------------------------------------------------------------------

class TestPoolIsValid:
    def test_empty_pool_is_valid(self):
        assert _pool_is_valid([], [])

    def test_single_recipe_always_valid(self):
        assert _pool_is_valid([r("A", ["x", "y"])], [])

    def test_two_recipes_sharing_one_ingredient_both_have_unique(self):
        # Tumbaga (Gold+Copper) and Brass (Copper+Zinc): each has a unique ingredient
        tumbaga = r("Tumbaga", ["Gold", "Copper"])
        brass = r("Brass", ["Copper", "Zinc"])
        assert _pool_is_valid([tumbaga, brass], [])

    def test_internal_collision_all_ingredients_covered(self):
        # Electrum (Gold+Silver) with Tumbaga (Gold+Copper) and Blue Alloy (Silver+Electrotine)
        # Electrum's Gold is covered by Tumbaga, Silver by Blue Alloy → collision
        electrum = r("Electrum", ["Gold", "Silver"])
        tumbaga = r("Tumbaga", ["Gold", "Copper"])
        blue = r("Blue Alloy", ["Silver", "Electrotine"])
        assert not _pool_is_valid([electrum, tumbaga, blue], [])

    def test_internal_safe_when_third_recipe_absent(self):
        # Without Tumbaga, Electrum + Blue Alloy is fine (each has a unique ingredient)
        electrum = r("Electrum", ["Gold", "Silver"])
        blue = r("Blue Alloy", ["Silver", "Electrotine"])
        assert _pool_is_valid([electrum, blue], [])

    def test_subset_recipe_triggers_collision(self):
        # Recipe A = {x}, Recipe B = {x, y} → A's sole ingredient is covered by B → collision
        a = r("A", ["x"])
        b = r("B", ["x", "y"])
        assert not _pool_is_valid([a, b], [])

    def test_external_collision_rest_recipe_covered(self):
        # Pool: Tumbaga + Blue Alloy. Rest: Electrum (Gold+Silver)
        # Pool union {Gold,Copper,Silver,Electrotine} covers Electrum {Gold,Silver}
        tumbaga = r("Tumbaga", ["Gold", "Copper"])
        blue = r("Blue Alloy", ["Silver", "Electrotine"])
        electrum = r("Electrum", ["Gold", "Silver"])
        assert not _pool_is_valid([tumbaga, blue], [electrum])

    def test_external_no_collision_rest_recipe_not_covered(self):
        # Same pool but rest has recipe needing an ingredient not in pool
        tumbaga = r("Tumbaga", ["Gold", "Copper"])
        blue = r("Blue Alloy", ["Silver", "Electrotine"])
        mystery = r("Mystery", ["Gold", "Unobtanium"])  # Unobtanium not in pool
        assert _pool_is_valid([tumbaga, blue], [mystery])

    def test_non_consumable_permanently_in_buffer(self):
        # Glass Tube: consumable=GlassDust, non_consumable=Mold
        # Glass Rod: consumable=[Mold, GlassDust]
        # Mold is always present from Glass Tube → Glass Rod's consumable inputs are covered
        glass_tube = r("Glass Tube", ["Glass Dust"], ["Mold"])
        glass_rod = r("Glass Rod", ["Mold", "Glass Dust"])
        assert not _pool_is_valid([glass_tube, glass_rod], [])

    def test_non_consumable_safe_when_not_consumed_by_others(self):
        # Glass Tube non-consumable Mold doesn't affect recipes that don't use Mold
        glass_tube = r("Glass Tube", ["Glass Dust"], ["Mold"])
        bronze = r("Bronze", ["Copper", "Tin"])
        assert _pool_is_valid([glass_tube, bronze], [])

    def test_non_consumable_contributes_to_rest_check(self):
        # Pool has recipe with non-consumable Mold.
        # Rest recipe needs (Mold + X). X is also in pool → rest recipe is covered.
        glass_tube = r("Glass Tube", ["Glass Dust"], ["Mold"])
        other = r("Other", ["Mold", "Glass Dust"])  # rest; Mold from NC, GlassDust from pool
        assert not _pool_is_valid([glass_tube], [other])

    def test_non_consumable_rest_not_covered_missing_ingredient(self):
        glass_tube = r("Glass Tube", ["Glass Dust"], ["Mold"])
        rest_recipe = r("Needs Rare", ["Mold", "Rare"])  # Rare not in pool → safe
        assert _pool_is_valid([glass_tube], [rest_recipe])

    def test_only_non_consumable_inputs_always_triggered(self):
        # A recipe with zero consumable inputs is always triggered once its
        # non-consumable is in the buffer (which it trivially is, since it's in the pool).
        # cons(R) = {} ⊆ anything → always unsafe with anything else in pool.
        always_on = r("AlwaysOn", [], ["SomeItem"])  # zero consumable inputs
        other = r("Other", ["X", "Y"])
        assert not _pool_is_valid([always_on, other], [])

    def test_only_non_consumable_alone_is_valid(self):
        always_on = r("AlwaysOn", [], ["SomeItem"])
        assert _pool_is_valid([always_on], [])


# ---------------------------------------------------------------------------
# assign_pools
# ---------------------------------------------------------------------------

class TestAssignPools:
    def test_empty_input(self):
        assert assign_pools([]) == []

    def test_single_recipe_one_pool(self):
        pools = assign_pools([r("A", ["x", "y"])])
        assert len(pools) == 1
        assert pools[0].recipes[0].name == "A"

    def test_non_conflicting_recipes_one_pool(self):
        pools = assign_pools([
            r("Tumbaga", ["Gold", "Copper"]),
            r("Blue Alloy", ["Silver", "Electrotine"]),
        ])
        assert len(pools) == 1

    def test_conflicting_recipes_split(self):
        # Electrum conflicts with both Tumbaga and Blue Alloy in the same pool
        pools = assign_pools([
            r("Tumbaga", ["Gold", "Copper"]),
            r("Blue Alloy", ["Silver", "Electrotine"]),
            r("Electrum", ["Gold", "Silver"]),
        ])
        # Electrum cannot share a pool with both Tumbaga and Blue Alloy
        for pool in pools:
            names = {recipe.name for recipe in pool.recipes}
            assert not ({"Electrum", "Tumbaga", "Blue Alloy"} <= names)

    def test_minimum_pools_five_copper_recipes(self):
        # All 5 copper recipes can coexist in one pool under the correct rule
        # (each has a unique non-copper ingredient; none covers another's inputs)
        copper_recipes = [
            r("Brass", ["Copper", "Zinc"]),
            r("Bronze", ["Copper", "Tin"]),
            r("Cupronickel", ["Copper", "Nickel"]),
            r("Red Alloy", ["Copper", "Redstone"]),
            r("Tumbaga", ["Gold", "Copper"]),
        ]
        pools = assign_pools(copper_recipes)
        assert len(pools) == 1

    def test_rest_splits_otherwise_valid_pool(self):
        # Tumbaga + Blue Alloy alone → 1 pool, but with Electrum in rest → 2 pools
        tumbaga = r("Tumbaga", ["Gold", "Copper"])
        blue = r("Blue Alloy", ["Silver", "Electrotine"])
        electrum = r("Electrum", ["Gold", "Silver"])

        without_rest = assign_pools([tumbaga, blue])
        with_rest = assign_pools([tumbaga, blue], rest=[electrum])

        assert len(without_rest) == 1
        assert len(with_rest) == 2

    def test_alloy_smelter_full_example(self):
        recipes = [
            r("Red Alloy", ["Copper", "Redstone"]),
            r("Cupronickel", ["Copper", "Nickel"]),
            r("Soldering Alloy", ["Tin", "Antimony"]),
            r("Electrum", ["Gold", "Silver"]),
            r("Brass", ["Copper", "Zinc"]),
            r("Invar", ["Iron", "Nickel"]),
            r("Blue Alloy", ["Silver", "Electrotine"]),
            r("Battery Alloy", ["Lead", "Antimony"]),
            r("Bronze", ["Copper", "Tin"]),
            r("Tumbaga", ["Gold", "Copper"]),
        ]
        pools = assign_pools(recipes)
        assert len(pools) == 2
        total = sum(len(p.recipes) for p in pools)
        assert total == len(recipes)

    def test_every_recipe_assigned_exactly_once(self):
        recipes = [
            r("A", ["x", "y"]),
            r("B", ["y", "z"]),
            r("C", ["z", "w"]),
            r("D", ["w", "x"]),
        ]
        pools = assign_pools(recipes)
        all_assigned = [rec.name for p in pools for rec in p.recipes]
        assert sorted(all_assigned) == sorted(r_.name for r_ in recipes)

    def test_deterministic_same_input_same_output(self):
        recipes = [
            r("Zinc Alloy", ["Zinc", "Copper"]),
            r("Antimony Mix", ["Antimony", "Lead"]),
            r("Bronze", ["Copper", "Tin"]),
            r("Invar", ["Iron", "Nickel"]),
            r("Electrum", ["Gold", "Silver"]),
        ]
        result1 = assign_pools(list(recipes))
        result2 = assign_pools(list(recipes))
        pools1 = [[rec.name for rec in p.recipes] for p in result1]
        pools2 = [[rec.name for rec in p.recipes] for p in result2]
        assert pools1 == pools2

    def test_pool_ids_sequential_from_one(self):
        recipes = [r("A", ["x"]), r("B", ["y"])]
        pools = assign_pools(recipes)
        ids = [p.id for p in pools]
        assert ids == list(range(1, len(pools) + 1))

    def test_recipes_within_pool_sorted_alphabetically(self):
        pools = assign_pools([
            r("Zinc", ["z", "a"]),
            r("Antimony", ["a", "b"]),
            r("Bronze", ["b", "c"]),
        ])
        for pool in pools:
            names = [rec.name for rec in pool.recipes]
            assert names == sorted(names, key=str.lower)

    def test_non_consumable_collision_forced_split(self):
        glass_tube = r("Glass Tube", ["Glass Dust"], ["Mold"])
        glass_rod = r("Glass Rod", ["Mold", "Glass Dust"])
        pools = assign_pools([glass_tube, glass_rod])
        assert len(pools) == 2

    def test_non_consumable_no_split_when_safe(self):
        glass_tube = r("Glass Tube", ["Glass Dust"], ["Mold"])
        bronze = r("Bronze", ["Copper", "Tin"])
        pools = assign_pools([glass_tube, bronze])
        assert len(pools) == 1
