from fontTools.ttLib import TTFont

from brand.logo import PALETTE
from brand.theme import theme_css
from brand.web_fonts import export_web_fonts


def test_web_fonts_are_latin_woff2_with_expected_weights(tmp_path):
    export_web_fonts(tmp_path)

    manrope = TTFont(tmp_path / "manrope.woff2")
    fraunces = TTFont(tmp_path / "fraunces.woff2")
    for font in (manrope, fraunces):
        assert font.flavor == "woff2"
        cmap = font.getBestCmap()
        for character in "éèàçœ€’ÉÀ":
            assert ord(character) in cmap, character
        assert ord("Ж") not in cmap

    weight_axis = next(axis for axis in manrope["fvar"].axes if axis.axisTag == "wght")
    assert (weight_axis.minValue, weight_axis.maxValue) == (400, 800)
    assert "fvar" not in fraunces


def test_theme_exposes_only_the_palette():
    css = theme_css()
    assert css.startswith("@theme {")
    assert "--color-*: initial;" in css
    for name, color in PALETTE.items():
        assert f"--color-{name}: {color};" in css
    assert '--font-sans: "Manrope"' in css
    assert '--font-douleur: "Fraunces"' in css
