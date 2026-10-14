from brand.logo import PALETTE


def theme_css() -> str:
    colors = "\n".join(f"  --color-{name}: {color};" for name, color in PALETTE.items())
    # --color-*: initial retire la palette par défaut de Tailwind : impossible d'utiliser une 5e teinte.
    return (
        "@theme {\n"
        "  --color-*: initial;\n"
        f"{colors}\n"
        '  --font-sans: "Manrope", system-ui, sans-serif;\n'
        '  --font-douleur: "Fraunces", Georgia, serif;\n'
        "}\n"
    )
