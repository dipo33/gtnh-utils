import pytest
from gtnh_utils.modes.recipes.model import Recipe, RecipePool


def test_all_inputs_union():
    r = Recipe("Foo", frozenset({"A", "B"}), frozenset({"C"}))
    assert r.all_inputs == frozenset({"A", "B", "C"})


def test_all_inputs_no_non_consumable():
    r = Recipe("Foo", frozenset({"A", "B"}))
    assert r.all_inputs == frozenset({"A", "B"})


def test_all_inputs_only_non_consumable():
    r = Recipe("Foo", frozenset(), frozenset({"Mold"}))
    assert r.all_inputs == frozenset({"Mold"})


def test_default_non_consumable_is_empty():
    r = Recipe("Foo", frozenset({"A"}))
    assert r.non_consumable == frozenset()


def test_recipe_is_frozen():
    r = Recipe("Foo", frozenset({"A"}))
    with pytest.raises((AttributeError, TypeError)):
        r.name = "Bar"  # type: ignore[misc]


def test_recipe_is_hashable():
    r1 = Recipe("Foo", frozenset({"A"}))
    r2 = Recipe("Foo", frozenset({"A"}))
    assert r1 == r2
    assert hash(r1) == hash(r2)
    assert len({r1, r2}) == 1


def test_pool_defaults():
    pool = RecipePool(id=1)
    assert pool.recipes == []
