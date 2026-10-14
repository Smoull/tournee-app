from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

FONTS_DIR = Path(__file__).parent / "fonts"
LATIN_UNICODES = (
    "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,"
    "U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"
)
# None = axe figé à sa valeur par défaut.
WEB_FONTS = {
    "manrope.woff2": ("Manrope.ttf", {"wght": (400, 800)}),
    "fraunces.woff2": ("Fraunces.ttf", {"wght": 600, "opsz": None, "SOFT": None, "WONK": None}),
}


def export_web_fonts(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for output_name, (source_name, axis_limits) in WEB_FONTS.items():
        font = TTFont(FONTS_DIR / source_name)
        options = subset.Options()
        options.layout_features = ["*"]
        subsetter = subset.Subsetter(options)
        subsetter.populate(unicodes=subset.parse_unicodes(LATIN_UNICODES))
        # Subset avant instanciation : l'instancer retire du gvar les glyphes sans variation,
        # ce que le subsetter ne supporte pas (KeyError).
        subsetter.subset(font)
        font = instancer.instantiateVariableFont(font, axis_limits)
        font.flavor = "woff2"
        font.save(out_dir / output_name)
