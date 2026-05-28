from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .model import RecipePool

_POOL_COLORS = ["cyan", "green", "yellow", "magenta", "blue", "red", "bright_white"]


def print_pools(pools: list[RecipePool], console: Console | None = None) -> None:
    if console is None:
        console = Console()

    console.print()
    console.print(f"[bold]Assigned [green]{len(pools)}[/green] pool(s)[/bold]")
    console.print()

    for pool in pools:
        color = _POOL_COLORS[(pool.id - 1) % len(_POOL_COLORS)]

        table = Table(
            box=box.ROUNDED,
            border_style=color,
            show_header=True,
            header_style=f"bold {color}",
            expand=False,
        )
        table.add_column("Recipe", style="bold white", no_wrap=True)
        table.add_column("Inputs", style="dim")

        for recipe in pool.recipes:
            inputs_str = " + ".join(sorted(recipe.inputs, key=str.lower))
            table.add_row(recipe.name, inputs_str)

        console.print(
            Panel(
                table,
                title=f"[bold {color}]Pool {pool.id}[/bold {color}]",
                border_style=color,
                expand=False,
            )
        )
        console.print()
