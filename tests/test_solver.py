"""
Tests for the pool assignment solver.

Naming convention for recipe helpers:
  r(name, inputs, non_consumable=(), fluid_inputs=())
"""
import pytest
from gtnh_utils.modes.recipes.model import Recipe
from gtnh_utils.modes.recipes.solver import assign_pools, _pool_is_valid


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def r(name: str, inputs, non_consumable=(), fluid_inputs=()) -> Recipe:
    return Recipe(name, frozenset(inputs), frozenset(non_consumable), frozenset(fluid_inputs))


# ---------------------------------------------------------------------------
# _pool_is_valid  (no-fluid cases unchanged)
# ---------------------------------------------------------------------------

class TestPoolIsValid:
    def test_empty_pool_is_valid(self):
        assert _pool_is_valid([], [])

    def test_single_recipe_always_valid(self):
        assert _pool_is_valid([r("A", ["x", "y"])], [])

    def test_two_recipes_sharing_one_ingredient_both_have_unique(self):
        tumbaga = r("Tumbaga", ["Gold", "Copper"])
        brass = r("Brass", ["Copper", "Zinc"])
        assert _pool_is_valid([tumbaga, brass], [])

    def test_internal_collision_all_ingredients_covered(self):
        electrum = r("Electrum", ["Gold", "Silver"])
        tumbaga = r("Tumbaga", ["Gold", "Copper"])
        blue = r("Blue Alloy", ["Silver", "Electrotine"])
        assert not _pool_is_valid([electrum, tumbaga, blue], [])

    def test_internal_safe_when_third_recipe_absent(self):
        electrum = r("Electrum", ["Gold", "Silver"])
        blue = r("Blue Alloy", ["Silver", "Electrotine"])
        assert _pool_is_valid([electrum, blue], [])

    def test_subset_recipe_triggers_collision(self):
        a = r("A", ["x"])
        b = r("B", ["x", "y"])
        assert not _pool_is_valid([a, b], [])

    def test_external_collision_rest_recipe_covered(self):
        tumbaga = r("Tumbaga", ["Gold", "Copper"])
        blue = r("Blue Alloy", ["Silver", "Electrotine"])
        electrum = r("Electrum", ["Gold", "Silver"])
        assert not _pool_is_valid([tumbaga, blue], [electrum])

    def test_external_no_collision_rest_recipe_not_covered(self):
        tumbaga = r("Tumbaga", ["Gold", "Copper"])
        blue = r("Blue Alloy", ["Silver", "Electrotine"])
        mystery = r("Mystery", ["Gold", "Unobtanium"])
        assert _pool_is_valid([tumbaga, blue], [mystery])

    def test_non_consumable_permanently_in_buffer(self):
        glass_tube = r("Glass Tube", ["Glass Dust"], ["Mold"])
        glass_rod = r("Glass Rod", ["Mold", "Glass Dust"])
        assert not _pool_is_valid([glass_tube, glass_rod], [])

    def test_non_consumable_safe_when_not_consumed_by_others(self):
        glass_tube = r("Glass Tube", ["Glass Dust"], ["Mold"])
        bronze = r("Bronze", ["Copper", "Tin"])
        assert _pool_is_valid([glass_tube, bronze], [])

    def test_non_consumable_contributes_to_rest_check(self):
        glass_tube = r("Glass Tube", ["Glass Dust"], ["Mold"])
        other = r("Other", ["Mold", "Glass Dust"])
        assert not _pool_is_valid([glass_tube], [other])

    def test_non_consumable_rest_not_covered_missing_ingredient(self):
        glass_tube = r("Glass Tube", ["Glass Dust"], ["Mold"])
        rest_recipe = r("Needs Rare", ["Mold", "Rare"])
        assert _pool_is_valid([glass_tube], [rest_recipe])

    def test_only_non_consumable_inputs_always_triggered(self):
        always_on = r("AlwaysOn", [], ["SomeItem"])
        other = r("Other", ["X", "Y"])
        assert not _pool_is_valid([always_on, other], [])

    def test_only_non_consumable_alone_is_valid(self):
        always_on = r("AlwaysOn", [], ["SomeItem"])
        assert _pool_is_valid([always_on], [])

    # --- fluid-aware validity tests ---

    def test_global_fluid_covers_recipe_consumable(self):
        # Recipe A needs solid X and fluid Water (global). Recipe B supplies X.
        # Water is global → always_present. B covers X → A is accidentally triggered.
        a = r("A", ["X"], fluid_inputs=["Water"])
        b = r("B", ["X", "Y"])
        assert not _pool_is_valid([a, b], [], global_fluids=frozenset({"water"}))

    def test_bound_fluid_not_covered_safe(self):
        # Recipe A needs solid X and bound fluid Water. Recipe B supplies X but not Water.
        # Water is bound (consumable), not in B → A is NOT accidentally triggered.
        a = r("A", ["X"], fluid_inputs=["Water"])
        b = r("B", ["X", "Y"])
        assert _pool_is_valid([a, b], [], bound_fluids_for_pool=frozenset({"water"}))

    def test_bound_fluid_shared_causes_collision(self):
        # Both A and B use bound fluid Water. When B runs (Water in tank), A's X
        # is covered by B → collision.
        a = r("A", ["X"], fluid_inputs=["Water"])
        b = r("B", ["X", "Y"], fluid_inputs=["Water"])
        assert not _pool_is_valid([a, b], [], bound_fluids_for_pool=frozenset({"water"}))

    def test_external_rest_fluid_covered_by_global(self):
        # Pool has recipe using solid X. Rest recipe needs X + fluid Water.
        # Water is global → rest recipe is fully covered → invalid.
        pool_r = r("Pool", ["X", "Y"])
        rest_r = r("Rest", ["X"], fluid_inputs=["Water"])
        assert not _pool_is_valid([pool_r], [rest_r], global_fluids=frozenset({"water"}))

    def test_external_rest_fluid_not_covered(self):
        # Same but Water is not global → rest recipe's fluid is missing → safe.
        pool_r = r("Pool", ["X", "Y"])
        rest_r = r("Rest", ["X"], fluid_inputs=["Water"])
        assert _pool_is_valid([pool_r], [rest_r])


# ---------------------------------------------------------------------------
# assign_pools  (no-fluid cases)
# ---------------------------------------------------------------------------

class TestAssignPools:
    def test_empty_input(self):
        result = assign_pools([])
        assert result.pools == []

    def test_single_recipe_one_pool(self):
        result = assign_pools([r("A", ["x", "y"])])
        assert len(result.pools) == 1
        assert result.pools[0].recipes[0].name == "A"

    def test_non_conflicting_recipes_one_pool(self):
        result = assign_pools([
            r("Tumbaga", ["Gold", "Copper"]),
            r("Blue Alloy", ["Silver", "Electrotine"]),
        ])
        assert len(result.pools) == 1

    def test_conflicting_recipes_split(self):
        result = assign_pools([
            r("Tumbaga", ["Gold", "Copper"]),
            r("Blue Alloy", ["Silver", "Electrotine"]),
            r("Electrum", ["Gold", "Silver"]),
        ])
        for pool in result.pools:
            names = {recipe.name for recipe in pool.recipes}
            assert not ({"Electrum", "Tumbaga", "Blue Alloy"} <= names)

    def test_minimum_pools_five_copper_recipes(self):
        copper_recipes = [
            r("Brass", ["Copper", "Zinc"]),
            r("Bronze", ["Copper", "Tin"]),
            r("Cupronickel", ["Copper", "Nickel"]),
            r("Red Alloy", ["Copper", "Redstone"]),
            r("Tumbaga", ["Gold", "Copper"]),
        ]
        result = assign_pools(copper_recipes)
        assert len(result.pools) == 1

    def test_rest_splits_otherwise_valid_pool(self):
        tumbaga = r("Tumbaga", ["Gold", "Copper"])
        blue = r("Blue Alloy", ["Silver", "Electrotine"])
        electrum = r("Electrum", ["Gold", "Silver"])

        without_rest = assign_pools([tumbaga, blue])
        with_rest = assign_pools([tumbaga, blue], rest=[electrum])

        assert len(without_rest.pools) == 1
        assert len(with_rest.pools) == 2

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
        result = assign_pools(recipes)
        assert len(result.pools) == 2
        total = sum(len(p.recipes) for p in result.pools)
        assert total == len(recipes)

    def test_every_recipe_assigned_exactly_once(self):
        recipes = [
            r("A", ["x", "y"]),
            r("B", ["y", "z"]),
            r("C", ["z", "w"]),
            r("D", ["w", "x"]),
        ]
        result = assign_pools(recipes)
        all_assigned = [rec.name for p in result.pools for rec in p.recipes]
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
        pools1 = [[rec.name for rec in p.recipes] for p in result1.pools]
        pools2 = [[rec.name for rec in p.recipes] for p in result2.pools]
        assert pools1 == pools2

    def test_pool_ids_sequential_from_one(self):
        recipes = [r("A", ["x"]), r("B", ["y"])]
        result = assign_pools(recipes)
        ids = [p.id for p in result.pools]
        assert ids == list(range(1, len(result.pools) + 1))

    def test_recipes_within_pool_sorted_alphabetically(self):
        result = assign_pools([
            r("Zinc", ["z", "a"]),
            r("Antimony", ["a", "b"]),
            r("Bronze", ["b", "c"]),
        ])
        for pool in result.pools:
            names = [rec.name for rec in pool.recipes]
            assert names == sorted(names, key=str.lower)

    def test_non_consumable_collision_forced_split(self):
        glass_tube = r("Glass Tube", ["Glass Dust"], ["Mold"])
        glass_rod = r("Glass Rod", ["Mold", "Glass Dust"])
        result = assign_pools([glass_tube, glass_rod])
        assert len(result.pools) == 2

    def test_non_consumable_no_split_when_safe(self):
        glass_tube = r("Glass Tube", ["Glass Dust"], ["Mold"])
        bronze = r("Bronze", ["Copper", "Tin"])
        result = assign_pools([glass_tube, bronze])
        assert len(result.pools) == 1


# ---------------------------------------------------------------------------
# assign_pools  (fluid cases)
# ---------------------------------------------------------------------------

class TestAssignPoolsFluids:
    def test_no_fluids_empty_fluid_state(self):
        result = assign_pools([r("A", ["x", "y"])])
        assert result.global_fluids == frozenset()
        assert result.bound_fluids == {}

    def test_safe_fluid_goes_global(self):
        # Recipe A: solid X + fluid Water. Recipe B: solid Y (no overlap with A).
        # Water being global doesn't cause any collision → should be global.
        a = r("A", ["X"], fluid_inputs=["Water"])
        b = r("B", ["Y"])
        result = assign_pools([a, b])
        assert len(result.pools) == 1
        assert "Water" in result.global_fluids

    def test_fluid_bound_when_global_would_cause_collision(self):
        # Recipe A: solid X + fluid Water.
        # Recipe B: solid X (also needs X, so if Water is global, B's X is covered
        # by A and Water is always there → but B has no fluid, so B's collision
        # depends on solid inputs only). Let's construct a case where global Water
        # triggers an external collision.
        # Rest recipe needs only Water → if Water is global it's always present,
        # and no other solid is needed → would be triggered → Water must be bound.
        a = r("A", ["X"], fluid_inputs=["Water"])
        rest = r("Rest", [], fluid_inputs=["Water"])  # needs ONLY Water
        result = assign_pools([a], rest=[rest])
        assert "Water" not in result.global_fluids
        assert 1 in result.bound_fluids
        assert "Water" in result.bound_fluids[1]

    def test_bound_fluid_associated_with_correct_pool(self):
        # Recipe A has no fluids; recipe B has fluid Water.
        # A rest recipe needing only Water prevents Water from being global.
        # Water should be bound to B's pool, not A's.
        rest = r("Rest", [], fluid_inputs=["Water"])  # forces Water to be bound
        a = r("A", ["X"])
        b = r("B", ["Y"], fluid_inputs=["Water"])
        result = assign_pools([a, b], rest=[rest])
        b_pool = next(p for p in result.pools if any(rc.name == "B" for rc in p.recipes))
        assert "Water" not in result.global_fluids
        assert b_pool.id in result.bound_fluids
        assert "Water" in result.bound_fluids[b_pool.id]

    def test_two_fluids_same_recipe_both_global_when_safe(self):
        a = r("A", ["X"], fluid_inputs=["Acid", "Base"])
        result = assign_pools([a])
        assert "Acid" in result.global_fluids
        assert "Base" in result.global_fluids

    def test_shared_solid_different_fluids_fits_one_pool(self):
        # Both recipes share solid X but have different fluids.
        # Old greedy approach: Water decided global when A is placed → B's {X}
        # is then covered by always_present(Water) + A's {X} → collision → 2 pools.
        # Two-phase: phase 1 treats both fluids as bound, so each recipe has a
        # unique consumable (Water vs Acid) → 1 pool. Phase 2 cannot promote
        # either fluid (would collapse the differentiator) → both stay bound.
        a = r("A", ["X"], fluid_inputs=["Water"])
        b = r("B", ["X"], fluid_inputs=["Acid"])
        result = assign_pools([a, b])
        assert len(result.pools) == 1
        assert "Water" not in result.global_fluids
        assert "Acid" not in result.global_fluids

    def test_casing_preserved_in_fluid_state(self):
        a = r("A", ["X"], fluid_inputs=["Sulfuric Acid"])
        result = assign_pools([a])
        all_fluids = result.global_fluids | frozenset().union(*result.bound_fluids.values())
        assert "Sulfuric Acid" in all_fluids

    def test_bound_fluid_in_correct_pool(self):
        rest = r("Rest", [], fluid_inputs=["Water"])
        recipe = r("Recipe", ["X"], fluid_inputs=["Water"])
        result = assign_pools([recipe], rest=[rest])
        assert len(result.pools) == 1
        pool_id = result.pools[0].id
        assert pool_id in result.bound_fluids
        assert "Water" in result.bound_fluids[pool_id]
