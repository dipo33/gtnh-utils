import textwrap
from pathlib import Path

import pytest

from gtnh_utils.modes.recipes.loader import load_recipes
from gtnh_utils.modes.recipes.model import Recipe


def write_yaml(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "recipes.yaml"
    p.write_text(textwrap.dedent(content))
    return p


def test_basic_load(tmp_path):
    path = write_yaml(tmp_path, """
        recipes:
          - name: Electrum
            inputs: [Gold, Silver]
    """)
    data = load_recipes(path)
    assert len(data.recipes) == 1
    assert data.recipes[0].name == "Electrum"
    assert data.recipes[0].inputs == frozenset({"Gold", "Silver"})
    assert data.recipes[0].non_consumable == frozenset()


def test_rest_section(tmp_path):
    path = write_yaml(tmp_path, """
        recipes:
          - name: Tumbaga
            inputs: [Gold, Copper]
        rest:
          - name: Electrum
            inputs: [Gold, Silver]
    """)
    data = load_recipes(path)
    assert len(data.recipes) == 1
    assert len(data.rest) == 1
    assert data.rest[0].name == "Electrum"


def test_missing_rest_section(tmp_path):
    path = write_yaml(tmp_path, """
        recipes:
          - name: Foo
            inputs: [A, B]
    """)
    data = load_recipes(path)
    assert data.rest == []


def test_non_consumable_parsed(tmp_path):
    path = write_yaml(tmp_path, """
        recipes:
          - name: Glass Tube
            inputs: [Glass Dust]
            non_consumable: [Mold (Ball)]
    """)
    data = load_recipes(path)
    r = data.recipes[0]
    assert r.inputs == frozenset({"Glass Dust"})
    assert r.non_consumable == frozenset({"Mold (Ball)"})


def test_missing_non_consumable_defaults_empty(tmp_path):
    path = write_yaml(tmp_path, """
        recipes:
          - name: Bronze
            inputs: [Copper, Tin]
    """)
    data = load_recipes(path)
    assert data.recipes[0].non_consumable == frozenset()


def test_sorted_alphabetically(tmp_path):
    path = write_yaml(tmp_path, """
        recipes:
          - name: Zinc Alloy
            inputs: [Zinc, X]
          - name: Antimony Mix
            inputs: [Antimony, Y]
          - name: Bronze
            inputs: [Copper, Tin]
    """)
    data = load_recipes(path)
    names = [r.name for r in data.recipes]
    assert names == sorted(names, key=str.lower)


def test_ingredient_case_preserved(tmp_path):
    path = write_yaml(tmp_path, """
        recipes:
          - name: Foo
            inputs: [UpperCase, MixedCase]
    """)
    data = load_recipes(path)
    assert "UpperCase" in data.recipes[0].inputs
    assert "MixedCase" in data.recipes[0].inputs
