# Tournée App — Conventions

Voir spec: [docs/superpowers/specs/2026-09-20-tournee-app-v1-design.md](docs/superpowers/specs/2026-09-20-tournee-app-v1-design.md)

## Principes

- **Single Responsibility en priorité** : code organisé en classes, une responsabilité par
  classe, un seul endroit à modifier si une règle change. Cette contrainte passe AVANT
  YAGNI/KISS en cas de conflit — voir arbitrage ci-dessous.
- **YAGNI** : pas de code pour un besoin hypothétique. Si V2 n'est pas confirmé, ne pas
  l'anticiper dans le code (la spec documente l'évolutivité, le code livre V1).
- **KISS** : solution la plus simple qui marche, à découpage de responsabilité égal.
  Pas de couche/config superflue au-delà de ce que SRP impose.
- Pas de commentaire sauf pour expliquer un POURQUOI non évident (contrainte cachée, workaround). Jamais de commentaire qui répète ce que le code dit déjà.
- **Fail fast, pas de fallback** : si quelque chose échoue (API, config, donnée invalide),
  ça doit échouer explicitement (exception/erreur remontée). Jamais de valeur par défaut
  silencieuse, de provider de secours, de `try/except` qui avale l'erreur ou de retour
  "dégradé" qui masque le problème.

### Arbitrage SRP vs YAGNI/KISS
Quand une implémentation "simple" (KISS) mélangerait plusieurs responsabilités dans un
même endroit (ex: calcul + appel API + persistance dans une seule fonction), découper en
classes séparées même si ça ajoute des fichiers/lignes. Exemple attendu côté backend:
- `FuelPriceService` (appel API gouv + cache) — seul endroit à changer si la source de
  prix carburant change
- `RoutingClient` (appel Mapbox) — seul endroit à changer si le provider routing change
  (cf. spec, migration OSRM possible en V2)
- `TourneeCalculator` (coût essence, coût total, heure fin) — logique pure, testée sans
  dépendance HTTP/DB
- Le découpage s'arrête dès qu'une classe a une seule raison de changer : ne pas fragmenter
  au-delà (une classe par ligne de code n'est pas l'objectif, YAGNI s'applique à la
  profondeur du découpage, pas à son existence).

## TDD — obligatoire

**Test écrit et rouge AVANT toute ligne d'implémentation, sur chaque feature/fix.**

Ordre systématique :
1. Écrire le test qui décrit le comportement attendu (backend: pytest / frontend: pas d'E2E V1, cf spec)
2. Lancer le test → doit échouer (rouge) — si il passe déjà, le test ne teste rien, le corriger
3. Implémenter le minimum pour faire passer le test (vert)
4. Refactor si besoin, tests toujours verts

Ne jamais écrire de code de prod sans test rouge correspondant écrit avant. Si une tâche semble trop petite pour un test ("juste un one-liner"), écrire le test quand même — c'est souvent là que les régressions silencieuses arrivent.

## Backend (FastAPI, Python, uv)

- Tests : `pytest`, mocks pour Mapbox + API gouv carburant (jamais d'appel réseau réel en test)
- Un test par cas de la section "Error handling" de la spec (adresse invalide, provider down, prix indisponible)
- Logique de calcul (coût essence, heure fin) testée en isolation, sans DB ni HTTP

## Frontend (Next.js)

- Pas d'E2E en V1 (scope spec) — vérification manuelle via le skill `run` avant de considérer une feature terminée
- Si logique non-triviale côté client (ex: calcul d'affichage, debounce reorder) → extraire en fonction pure testable (vitest), même règle TDD

## Avant de considérer une feature "terminée"

- Tests écrits avant le code, tous verts
- Vérification manuelle dans le navigateur pour tout changement UI (skill `run`)
- Rien d'ajouté qui n'est pas dans la spec V1 (YAGNI)

## Identité visuelle (validée)

4 couleurs, aucune 5e teinte (variations d'opacité autorisées). Source unique en code :
`PALETTE` dans `landing/brand/logo.py`, reprise en tokens Tailwind.

| Rôle | Couleur | Usage |
|---|---|---|
| Fond | `#11181C` ardoise sombre | fond de page (sombre = expertise) |
| Texte | `#E6EAEA` blanc cassé | texte courant |
| Principale | `#3E9C8A` vert-bleu | logo, titres, marque |
| Accent | `#F2A93B` ambre | CTA, compteur de places, prix early access uniquement |

Tout changement de couleur revérifie WCAG AA puis régénère les assets : `uv run python -m brand.export` (depuis `landing/`).

### Typographie (validée)

3 familles, chacune a un rôle : elles guident la lecture et structurent la page. Aucune autre police.
Toutes sous licence SIL OFL 1.1, auto-hébergées en woff2 (subset latin), jamais via CDN (RGPD).

| Police | Rôle | Graisses |
|---|---|---|
| Manrope | nom à côté du logo, titres de section (H2/H3), texte courant, prix, formulaire | 400, 700 |
| Fraunces | phrase de douleur (H1 hero, accroches douleur) uniquement | 600 |
| Bricolage Grotesque | CTA uniquement | 700 |
