from pathlib import Path

import click
from rich.console import Console


@click.group()
def cli() -> None:
    """GTNH Utils — a collection of tools for GregTech: New Horizons."""


@cli.command("recipes")
@click.argument("input_file", metavar="FILE", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    metavar="FILE",
    type=click.Path(path_type=Path),
    default=None,
    help="Output YAML file (default: <input>_pools.yaml).",
)
def recipes_cmd(input_file: Path, output: Path | None) -> None:
    """Assign recipes from FILE to conflict-free pools.

    Two recipes conflict when they share at least one input ingredient — placing
    them in the same machine pool would allow accidental mis-crafting.  The
    tool finds the minimum number of pools required so that every pool is
    conflict-free, then writes the assignment to a YAML file.
    """
    from .modes.recipes.formatter import print_pools
    from .modes.recipes.loader import load_recipes
    from .modes.recipes.solver import assign_pools
    from .modes.recipes.writer import write_pools

    console = Console()

    recipes = load_recipes(input_file)
    console.print(f"[dim]Loaded [bold]{len(recipes)}[/bold] recipe(s) from [italic]{input_file}[/italic][/dim]")

    pools = assign_pools(recipes)
    print_pools(pools, console)

    if output is None:
        output = input_file.parent / f"{input_file.stem}_pools.yaml"

    write_pools(pools, output)
    console.print(f"[dim]Output written to [bold italic]{output}[/bold italic][/dim]\n")
