from rich import box
from rich.console import Console, Group
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table

from .model import SolverResult

_POOL_COLORS = ["cyan", "green", "yellow", "magenta", "blue", "red", "bright_white"]


def print_pools(result: SolverResult, console: Console | None = None) -> None:
    if console is None:
        console = Console()

    pools = result.pools
    global_fluids = result.global_fluids
    bound_fluids = result.bound_fluids

    console.print()
    console.print(f"[bold]Assigned [green]{len(pools)}[/green] pool(s)[/bold]")
    console.print()

    if global_fluids:
        fluid_list = "  ".join(sorted(global_fluids, key=str.lower))
        console.print(
            Panel(
                f"[dim]{fluid_list}[/dim]",
                title="[bold]Global Tanks[/bold]",
                border_style="white",
                expand=False,
            )
        )
        console.print()

    for pool in pools:
        color = _POOL_COLORS[(pool.id - 1) % len(_POOL_COLORS)]
        has_nc = any(r.non_consumable for r in pool.recipes)
        has_fluids = any(r.fluid_inputs for r in pool.recipes)
        pool_bound = bound_fluids.get(pool.id, frozenset())

        table = Table(
            box=box.ROUNDED,
            border_style=color,
            show_header=True,
            header_style=f"bold {color}",
            expand=False,
        )
        table.add_column("Recipe", style="bold white", no_wrap=True)
        table.add_column("Inputs", style="dim")
        if has_nc:
            table.add_column("Non-consumable", style="dim italic")
        if has_fluids:
            table.add_column("Fluid Inputs", style="dim cyan")

        for recipe in pool.recipes:
            inputs_str = " + ".join(sorted(recipe.inputs, key=str.lower))
            row = [recipe.name, inputs_str]
            if has_nc:
                row.append(" + ".join(sorted(recipe.non_consumable, key=str.lower)))
            if has_fluids:
                row.append(" + ".join(sorted(recipe.fluid_inputs, key=str.lower)))
            table.add_row(*row)

        if pool_bound:
            bound_str = "Bound tanks: " + "  ".join(sorted(pool_bound, key=str.lower))
            content = Group(table, Padding(f"[dim italic]{bound_str}[/dim italic]", (0, 1)))
        else:
            content = table

        console.print(
            Panel(
                content,
                title=f"[bold {color}]Pool {pool.id}[/bold {color}]",
                border_style=color,
                expand=False,
            )
        )
        console.print()
