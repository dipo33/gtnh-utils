from dataclasses import dataclass, field
from typing import NamedTuple


@dataclass(frozen=True)
class Recipe:
    name: str
    inputs: frozenset[str]
    non_consumable: frozenset[str] = field(default_factory=frozenset)
    fluid_inputs: frozenset[str] = field(default_factory=frozenset)

    @property
    def all_inputs(self) -> frozenset[str]:
        return self.inputs | self.non_consumable | self.fluid_inputs


@dataclass
class RecipePool:
    id: int
    recipes: list[Recipe] = field(default_factory=list)


class SolverResult(NamedTuple):
    pools: list[RecipePool]
    global_fluids: frozenset[str]            # original casing
    bound_fluids: dict[int, frozenset[str]]  # pool_id -> frozenset of fluids (original casing)
