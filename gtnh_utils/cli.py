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

    The input YAML has two sections:

    \b
      recipes  — recipes to automate; these are assigned to pools.
      rest     — other recipes the machine knows about (optional); never
                 assigned to a pool but used to detect accidental crafting.
    """
    from .modes.recipes.formatter import print_pools
    from .modes.recipes.loader import load_recipes
    from .modes.recipes.solver import assign_pools
    from .modes.recipes.writer import write_pools

    console = Console()

    data = load_recipes(input_file)

    rest_note = f", [bold]{len(data.rest)}[/bold] rest" if data.rest else ""
    console.print(
        f"[dim]Loaded [bold]{len(data.recipes)}[/bold] recipe(s) to automate{rest_note}"
        f" from [italic]{input_file}[/italic][/dim]"
    )

    pools = assign_pools(data.recipes, data.rest)
    print_pools(pools, console)

    if output is None:
        output = input_file.parent / f"{input_file.stem}_pools.yaml"

    write_pools(pools, output)
    console.print(f"[dim]Output written to [bold italic]{output}[/bold italic][/dim]\n")
