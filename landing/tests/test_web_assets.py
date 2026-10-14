from fontTools.ttLib import TTFont

from brand.logo import PALETTE
from brand.theme import theme_css
from brand.web_fonts import export_web_fonts


def test_only_manrope_is_exported_as_latin_woff2(tmp_path):
    export_web_fonts(tmp_path)

    assert sorted(path.name for path in tmp_path.iterdir()) == ["manrope.woff2"]
    manrope = TTFont(tmp_path / "manrope.woff2")
    assert manrope.flavor == "woff2"
    cmap = manrope.getBestCmap()
    for character in "éèàçœ€’ÉÀ":
        assert ord(character) in cmap, character
    assert ord("Ж") not in cmap
    weight_axis = next(axis for axis in manrope["fvar"].axes if axis.axisTag == "wght")
    assert (weight_axis.minValue, weight_axis.maxValue) == (400, 800)


def test_theme_exposes_only_the_palette():
    css = theme_css()
    assert css.startswith("@theme {")
    assert "--color-*: initial;" in css
    for name, color in PALETTE.items():
        assert f"--color-{name}: {color};" in css
    assert '--font-sans: "Manrope"' in css
    assert "Fraunces" not in css
    assert "--font-douleur" not in css
