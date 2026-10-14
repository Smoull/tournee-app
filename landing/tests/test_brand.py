import re

from PIL import Image

from brand.export import export_brand_assets
from brand.logo import PALETTE, logo_svg


def test_logo_uses_only_palette_colors():
    used = set(re.findall(r"#[0-9A-Fa-f]{6}", logo_svg()))
    assert used and used <= set(PALETTE.values())


def test_logo_monochrome_uses_text_color_only():
    svg = logo_svg(monochrome=True)
    assert PALETTE["principale"] not in svg
    assert PALETTE["accent"] not in svg


def test_logo_progress_zero_hides_route():
    assert 'stroke-dashoffset="0.0"' in logo_svg(progress=1)
    assert 'stroke-dashoffset="0.0"' not in logo_svg(progress=0)


def test_export_produces_all_assets_at_expected_sizes(tmp_path):
    export_brand_assets(tmp_path)

    expected_png = {
        "apple-touch-icon.png": (180, 180),
        "icon-192.png": (192, 192),
        "icon-512.png": (512, 512),
        "og-image.png": (1200, 630),
    }
    for name, size in expected_png.items():
        assert Image.open(tmp_path / name).size == size, name

    assert (tmp_path / "logo.svg").read_text().startswith("<svg")
    assert (tmp_path / "logo-mono.svg").read_text().startswith("<svg")
    assert (tmp_path / "favicon.svg").read_text().startswith("<svg")

    ico = Image.open(tmp_path / "favicon.ico")
    assert {(16, 16), (32, 32), (48, 48)} <= set(ico.info["sizes"])

    for name in ("logo.gif", "logo-halo.gif"):
        gif = Image.open(tmp_path / name)
        assert gif.size == (250, 250), name
        assert gif.n_frames > 1, name
        assert gif.info["loop"] == 0, name


def test_og_image_shows_name_and_tagline_next_to_logo(tmp_path):
    export_brand_assets(tmp_path)

    og = Image.open(tmp_path / "og-image.png").convert("RGB")
    text_area = og.crop((820, 150, 1150, 480))
    background = tuple(int(PALETTE["fond"][i : i + 2], 16) for i in (1, 3, 5))
    assert any(pixel != background for pixel in text_area.get_flattened_data())
