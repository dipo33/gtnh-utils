from __future__ import annotations

import json
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def run(json_path: Path, output_path: Path, console: Console) -> None:
    with open(json_path) as f:
        entries = json.load(f)

    console.print()
    console.print(
        f"[dim]Loaded [bold]{len(entries)}[/bold] recipe(s)"
        f" from [italic]{json_path}[/italic][/dim]"
    )

    _print_preview(entries, console)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_yaml(entries, output_path)
    console.print(f"[dim]Output written to [bold italic]{output_path}[/bold italic][/dim]\n")


def _print_preview(entries: list[dict], console: Console) -> None:
    has_fluids = any(e.get("fluidInputs") for e in entries)
    has_nc = any(_nc_parts(e) for e in entries)

    table = Table(
        box=box.ROUNDED,
        border_style="cyan",
        show_header=True,
        header_style="bold cyan",
        expand=False,
    )
    table.add_column("Recipe", style="bold white", no_wrap=True)
    table.add_column("Inputs", style="dim")
    if has_nc:
        table.add_column("Non-consumable", style="dim italic")
    if has_fluids:
        table.add_column("Fluid Inputs", style="dim cyan")

    for entry in entries:
        results = entry.get("results", [])
        name = results[0]["localizedName"] if results else "?"

        inputs_str = " + ".join(i["localizedName"] for i in entry.get("inputs", []))

        row = [name, inputs_str]
        if has_nc:
            row.append(" + ".join(_nc_parts(entry)))
        if has_fluids:
            row.append(" + ".join(fi["localizedName"] for fi in entry.get("fluidInputs", [])))

        table.add_row(*row)

    console.print()
    console.print(
        Panel(
            table,
            title="[bold cyan]Imported Recipes[/bold cyan]",
            border_style="cyan",
            expand=False,
        )
    )
    console.print()


def _nc_parts(entry: dict) -> list[str]:
    parts = []
    circuit = entry.get("circuit")
    if circuit is not None:
        parts.append(f"Circuit ({circuit})")
    shape = entry.get("shape")
    if shape:
        parts.append(shape)
    mold = entry.get("mold")
    if mold:
        parts.append(mold)
    parts.extend(entry.get("nonConsumable", []))
    return parts


def _write_yaml(entries: list[dict], path: Path) -> None:
    lines = ["recipes:"]
    for entry in entries:
        lines.append("")
        for line in _recipe_lines(entry):
            lines.append("  " + line)
    lines.append("")
    path.write_text("\n".join(lines))


def _recipe_lines(entry: dict) -> list[str]:
    lines = []

    results = entry.get("results", [])
    primary = results[0]["localizedName"] if results else "Unknown"
    lines.append(f"- name: {primary}")
    for r in results[1:]:
        lines.append(f"  # name: {r['localizedName']}")

    inputs = entry.get("inputs", [])
    if inputs:
        lines.append("  inputs: [{}]".format(", ".join(i["localizedName"] for i in inputs)))

    fluid_inputs = entry.get("fluidInputs", [])
    if fluid_inputs:
        lines.append("  fluid_inputs: [{}]".format(", ".join(fi["localizedName"] for fi in fluid_inputs)))

    nc = _nc_parts(entry)
    if nc:
        lines.append("  non_consumable: [{}]".format(", ".join(nc)))

    return lines
