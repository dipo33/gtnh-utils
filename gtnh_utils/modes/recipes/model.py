from dataclasses import dataclass, field


@dataclass(frozen=True)
class Recipe:
    name: str
    inputs: frozenset[str]


@dataclass
class RecipePool:
    id: int
    recipes: list[Recipe] = field(default_factory=list)
