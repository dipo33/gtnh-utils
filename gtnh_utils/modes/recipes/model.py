from dataclasses import dataclass, field


@dataclass(frozen=True)
class Recipe:
    name: str
    inputs: frozenset[str]
    non_consumable: frozenset[str] = field(default_factory=frozenset)

    @property
    def all_inputs(self) -> frozenset[str]:
        return self.inputs | self.non_consumable


@dataclass
class RecipePool:
    id: int
    recipes: list[Recipe] = field(default_factory=list)
