# Tournée App — Conventions

Voir spec: [docs/superpowers/specs/2026-09-20-tournee-app-v1-design.md](docs/superpowers/specs/2026-09-20-tournee-app-v1-design.md)

## Principes

- **YAGNI** : pas de code pour un besoin hypothétique. Si V2 n'est pas confirmé, ne pas l'anticiper dans le code (la spec documente l'évolutivité, le code livre V1).
- **KISS** : solution la plus simple qui marche. Pas d'abstraction/couche/config avant qu'un deuxième cas d'usage réel l'exige.
- Pas de commentaire sauf pour expliquer un POURQUOI non évident (contrainte cachée, workaround). Jamais de commentaire qui répète ce que le code dit déjà.

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
