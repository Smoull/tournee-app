PALETTE = {
    "fond": "#11181C",
    "texte": "#E6EAE8",
    "principale": "#3E9C8A",
    "accent": "#F2A93B",
}

ROUTE = "M24 76 H60 A14 14 0 0 0 60 48 H40 A14 14 0 0 1 40 20 H76"
ROUTE_LENGTH = 180.0
# (x, y, position du point sur la route en fraction de ROUTE_LENGTH)
START_STOP = (24, 76, 0.0)
MIDDLE_STOP = (50, 48, 0.5)
ARRIVAL_STOP = (76, 20, 1.0)


def logo_svg(progress: float = 1.0, halo_opacity: float = 0.35, monochrome: bool = False) -> str:
    route_color = PALETTE["texte"] if monochrome else PALETTE["principale"]
    arrival_color = PALETTE["texte"] if monochrome else PALETTE["accent"]
    stop_color = PALETTE["texte"]
    dash_offset = ROUTE_LENGTH * (1 - progress)

    parts = [
        f'<path d="{ROUTE}" fill="none" stroke="{route_color}" stroke-width="7" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'stroke-dasharray="{ROUTE_LENGTH}" stroke-dashoffset="{dash_offset:.1f}"/>'
    ]
    for x, y, position in (START_STOP, MIDDLE_STOP):
        if progress >= position:
            parts.append(f'<circle cx="{x}" cy="{y}" r="6.5" fill="{stop_color}"/>')
    x, y, position = ARRIVAL_STOP
    if progress >= position:
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="13" fill="none" stroke="{arrival_color}" '
            f'stroke-width="2.5" opacity="{halo_opacity:.2f}"/>'
        )
        parts.append(f'<circle cx="{x}" cy="{y}" r="8" fill="{arrival_color}"/>')

    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">{"".join(parts)}</svg>'
