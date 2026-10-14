from functools import cache

from markupsafe import Markup

from tools.vendor_assets import ICONS, ICONS_DIR


@cache
def _svg(name: str) -> str:
    return (ICONS_DIR / f"{name}.svg").read_text().strip()


def icon(name: str, css_class: str = "size-6") -> Markup:
    if name not in ICONS:
        raise ValueError(f"icône inconnue : {name} (liste fermée dans tools/vendor_assets.py)")
    attributes = f'class="{css_class}" aria-hidden="true" focusable="false" '
    return Markup(_svg(name).replace("<svg ", f"<svg {attributes}", 1))
