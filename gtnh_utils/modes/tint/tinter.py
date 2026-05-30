import numpy as np
from PIL import Image


def parse_color(color: str) -> tuple[int, int, int]:
    """Parse a hex color string (#RRGGBB or RRGGBB) into (r, g, b)."""
    color = color.lstrip("#")
    if len(color) != 6:
        raise ValueError(f"Color must be 6 hex digits, got: {color!r}")
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    return r, g, b


def tint_texture(image_path: str, tint_rgb: tuple[int, int, int]) -> Image.Image:
    """Apply Minecraft-style GL_MODULATE tint to a grayscale texture."""
    tint = np.array(tint_rgb, dtype=np.uint16)
    img = Image.open(image_path).convert("RGBA")
    arr = np.array(img, dtype=np.uint16)
    arr[..., :3] = (arr[..., :3] * tint) // 255
    return Image.fromarray(arr.astype(np.uint8), "RGBA")
