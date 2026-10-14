# Landing Bouclé.tech

Tout se lance depuis `landing/` avec uv.

1. `cp secret.toml.example secret.toml` (phase 1 : `LEAD_STORE = "memory"`, les leads sont perdus au redémarrage)
2. `uv run python -m brand.export` : logos, favicons, og-image, GIF, polices woff2, tokens Tailwind
3. `TAILWINDCSS_VERSION=v4.1.11 uv run tailwindcss -i app/static_src/input.css -o static/css/app.css --minify`
4. `uv run uvicorn app.main:app --reload` puis http://127.0.0.1:8000

Tests : `uv run pytest -q`
