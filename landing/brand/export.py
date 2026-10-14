import io
import math
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFont

from brand.identity import DOMAIN_SUFFIX, NAME, TAGLINE
from brand.logo import PALETTE, logo_svg

GIF_SIZE = 250
GIF_DRAW_FRAMES = 30
GIF_BREATH_FRAMES = 30
GIF_FRAME_MS = 50
FONTS_DIR = Path(__file__).parent / "fonts"
SUFFIX_RATIO = 0.5


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


def _font(file_name: str, size: int, weight: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(FONTS_DIR / file_name, size)
    font.set_variation_by_axes(
        [weight if axis["name"] in (b"Weight", "Weight") else axis["default"] for axis in font.get_variation_axes()]
    )
    return font


def wordmark_sizes(name_size: int) -> tuple[int, int]:
    return name_size, round(name_size * SUFFIX_RATIO)


def _og_image() -> Image.Image:
    width, height, logo_size = 1200, 630, 300
    image = Image.new("RGBA", (width, height), PALETTE["fond"])
    logo = _render(logo_svg(), logo_size, logo_size)
    image.paste(logo, (110, (height - logo_size) // 2), logo)
    draw = ImageDraw.Draw(image)
    name_size, suffix_size = wordmark_sizes(110)
    name_font = _font("Manrope.ttf", name_size, 800)
    baseline = 300
    draw.text((470, baseline), NAME, font=name_font, fill=PALETTE["texte"], anchor="ls")
    suffix_x = 470 + draw.textlength(NAME, font=name_font) + 4
    draw.text((suffix_x, baseline), DOMAIN_SUFFIX, font=_font("Manrope.ttf", suffix_size, 700), fill=PALETTE["texte"], anchor="ls")
    draw.text((474, baseline + 75), TAGLINE, font=_font("Fraunces.ttf", 46, 600), fill=PALETTE["texte"], anchor="ls")
    return image


def _breathing_svgs() -> list[str]:
    # Halo qui "respire" lentement à l'arrivée : l'image de tranquillité une fois la tournée bouclée.
    return [
        logo_svg(halo_opacity=0.2 + 0.5 * (1 - math.cos(2 * math.pi * i / GIF_BREATH_FRAMES)) / 2)
        for i in range(GIF_BREATH_FRAMES)
    ]


def _save_gif(svgs: list[str], path: Path) -> None:
    logo_size = int(GIF_SIZE * 0.8)
    first, *rest = [
        _render(_on_background(svg, GIF_SIZE, GIF_SIZE, logo_size), GIF_SIZE, GIF_SIZE).convert("RGB")
        for svg in svgs
    ]
    first.save(path, save_all=True, append_images=rest, duration=GIF_FRAME_MS, loop=0, optimize=True)


def export_brand_assets(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    logo = logo_svg()

    (out_dir / "logo.svg").write_text(logo)
    (out_dir / "logo-mono.svg").write_text(logo_svg(monochrome=True))
    (out_dir / "favicon.svg").write_text(logo)

    _render(logo, 48, 48).save(out_dir / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])

    for name, size in (("apple-touch-icon.png", 180), ("icon-192.png", 192), ("icon-512.png", 512)):
        _render(_on_background(logo, size, size, int(size * 0.8)), size, size).save(out_dir / name)

    _og_image().save(out_dir / "og-image.png")

    drawing = [logo_svg(progress=(i + 1) / GIF_DRAW_FRAMES) for i in range(GIF_DRAW_FRAMES)]
    _save_gif(drawing + _breathing_svgs(), out_dir / "logo.gif")
    _save_gif(_breathing_svgs(), out_dir / "logo-halo.gif")


if __name__ == "__main__":
    export_brand_assets(Path(__file__).parent.parent / "static" / "brand")
