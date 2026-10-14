import io
import math
from pathlib import Path

import cairosvg
from PIL import Image

from brand.logo import PALETTE, logo_svg

GIF_SIZE = 250
GIF_DRAW_FRAMES = 30
GIF_BREATH_FRAMES = 30
GIF_FRAME_MS = 50


def _on_background(svg: str, width: int, height: int, logo_size: int) -> str:
    x = (width - logo_size) / 2
    y = (height - logo_size) / 2
    inner = svg.replace("<svg ", f'<svg x="{x}" y="{y}" width="{logo_size}" height="{logo_size}" ', 1)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
        f'<rect width="100%" height="100%" fill="{PALETTE["fond"]}"/>{inner}</svg>'
    )


def _render(svg: str, width: int, height: int) -> Image.Image:
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=width, output_height=height)
    return Image.open(io.BytesIO(png)).convert("RGBA")


def _gif_frames() -> list[Image.Image]:
    drawing = [logo_svg(progress=(i + 1) / GIF_DRAW_FRAMES) for i in range(GIF_DRAW_FRAMES)]
    # Halo qui "respire" lentement à l'arrivée : l'image de tranquillité une fois la tournée bouclée.
    breathing = [
        logo_svg(halo_opacity=0.2 + 0.5 * (1 - math.cos(2 * math.pi * i / GIF_BREATH_FRAMES)) / 2)
        for i in range(GIF_BREATH_FRAMES)
    ]
    logo_size = int(GIF_SIZE * 0.8)
    return [
        _render(_on_background(svg, GIF_SIZE, GIF_SIZE, logo_size), GIF_SIZE, GIF_SIZE).convert("RGB")
        for svg in drawing + breathing
    ]


def export_brand_assets(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    logo = logo_svg()

    (out_dir / "logo.svg").write_text(logo)
    (out_dir / "logo-mono.svg").write_text(logo_svg(monochrome=True))
    (out_dir / "favicon.svg").write_text(logo)

    _render(logo, 48, 48).save(out_dir / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])

    for name, size in (("apple-touch-icon.png", 180), ("icon-192.png", 192), ("icon-512.png", 512)):
        _render(_on_background(logo, size, size, int(size * 0.8)), size, size).save(out_dir / name)

    _render(_on_background(logo, 1200, 630, 360), 1200, 630).save(out_dir / "og-image.png")

    first, *rest = _gif_frames()
    first.save(
        out_dir / "logo.gif", save_all=True, append_images=rest, duration=GIF_FRAME_MS, loop=0, optimize=True
    )


if __name__ == "__main__":
    export_brand_assets(Path(__file__).parent.parent / "static" / "brand")
