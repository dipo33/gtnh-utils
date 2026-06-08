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

    result = assign_pools(data.recipes, data.rest)
    print_pools(result, console)

    if output is None:
        parts = input_file.parts
        if "inputs" in parts:
            idx = list(parts).index("inputs")
            out_parts = parts[:idx] + ("outputs",) + parts[idx + 1:]
            output = Path(*out_parts).with_name(f"{input_file.stem}_pools.yaml")
        else:
            output = input_file.parent / f"{input_file.stem}_pools.yaml"

    output.parent.mkdir(parents=True, exist_ok=True)
    write_pools(result, output)
    console.print(f"[dim]Output written to [bold italic]{output}[/bold italic][/dim]\n")


@cli.command("tint")
@click.argument("texture", metavar="FILE", type=click.Path(exists=True, path_type=Path))
@click.argument("color", metavar="COLOR")
@click.option(
    "--output",
    "-o",
    metavar="FILE",
    type=click.Path(path_type=Path),
    default=None,
    help="Output PNG file (default: <texture>_<color>.png in outputs/textures/).",
)
def tint_cmd(texture: Path, color: str, output: Path | None) -> None:
    """Apply a Minecraft-style color tint to a grayscale texture.

    COLOR is a hex RGB value, with or without a leading #.

    \b
    Examples:
      tool.py tint inputs/textures/leaves.png 80A755
      tool.py tint inputs/textures/leaves.png "#619961"
    """
    from .modes.tint.tinter import parse_color, tint_texture

    console = Console()

    try:
        tint_rgb = parse_color(color)
    except ValueError as exc:
        raise click.BadParameter(str(exc), param_hint="COLOR") from exc

    normalized = color.lstrip("#").upper()
    console.print(
        f"[dim]Tinting [italic]{texture}[/italic] with"
        f" [bold]#{normalized}[/bold] ({tint_rgb[0]}, {tint_rgb[1]}, {tint_rgb[2]})[/dim]"
    )

    img = tint_texture(str(texture), tint_rgb)

    if output is None:
        parts = texture.parts
        if "inputs" in parts:
            idx = list(parts).index("inputs")
            out_parts = parts[:idx] + ("outputs",) + parts[idx + 1:]
            output = Path(*out_parts).with_name(f"{texture.stem}_{normalized}.png")
        else:
            output = texture.parent / f"{texture.stem}_{normalized}.png"

    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output), "PNG")
    console.print(f"[dim]Output written to [bold italic]{output}[/bold italic][/dim]\n")
