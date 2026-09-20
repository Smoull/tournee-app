# Tournée App — V1 Design (sans optimisation)

## Contexte
Webapp SaaS pour artisans/pros terrain : gérer tournée du jour (trajets clients),
calculer coût essence + heure de fin estimée. Design haut de gamme, animé.
Blog SEO traité en spec séparée (hors scope V1).

## Objectifs V1
- Profil véhicule (conso + carburant), une fois
- Prix carburant auto (moyenne glissante 7j, API gouv)
- Ajout trajets du jour un par un, adresse + durée chantier, ordre manuel (drag)
- Calcul: coût essence/trajet, coût total jour, heure de fin estimée
- Auth SSO Google/Facebook + email/password
- UI "mega pro", animée (SaaS-grade)

Hors scope V1: optimisation d'itinéraire, multi-véhicules simultanés, blog.

## Architecture

```
[Next.js frontend] --REST--> [FastAPI backend] --> [OSRM/Nominatim (Docker)]
        |                          |
        |                          --> [API gouv prix-carburants]
        |
        --> [Supabase Cloud: Auth + Postgres]
```

- **Frontend**: Next.js (App Router, TS), Tailwind, Framer Motion. Consomme Supabase Auth
  directement (session JWT), appelle FastAPI pour logique métier (calc).
- **Backend**: FastAPI (Python, géré par `uv`). Endpoints: vehicle profile CRUD, tournée
  CRUD, calc trajet (géocodage + distance + coût), refresh prix carburant.
- **Auth + DB**: Supabase Cloud (Postgres managé + Auth SSO Google/Facebook/email).
  Backend FastAPI valide le JWT Supabase sur chaque requête, lit/écrit direct dans
  le Postgres Supabase (via SQLAlchemy + connection string Supabase).
- **Routing/Géocodage**: OSRM + Nominatim self-hosted en Docker (docker-compose),
  appelés par le backend FastAPI. Extrait France (ou région du user) pour limiter la taille.
- **Infra**: `docker-compose.yml` (osrm, nominatim, api). Frontend déployé séparément
  (Vercel ou même compose). `uv` pour gestion deps Python du backend.

## Data model (Postgres, schéma `public`, RLS activé par user_id)

```sql
vehicle_profiles (
  id uuid pk, user_id uuid fk auth.users, nom text,
  conso_l_100km numeric, type_carburant text  -- gazole|sp95|sp98|e10|e85|gplc
)

fuel_price_cache (
  type_carburant text pk, prix_moyen_7j numeric, date_maj timestamptz
)

tournees (
  id uuid pk, user_id uuid fk, date date, heure_debut time, statut text
)

trajets (
  id uuid pk, tournee_id uuid fk, ordre int, adresse text, lat numeric, lon numeric,
  duree_chantier_min int,
  distance_km numeric,      -- calculé (OSRM depuis point précédent, ou départ véhicule)
  duree_trajet_min numeric, -- calculé (OSRM)
  cout_essence numeric      -- calculé: distance_km * (conso/100) * prix_carburant
)
```

## Logique de calcul
1. Trigger: ajout/reorder d'un trajet → backend recalcule distance/durée via OSRM
   entre trajet précédent (ou point de départ) et ce trajet.
2. `cout_essence = distance_km * (conso_l_100km / 100) * prix_moyen_7j`
3. `cout_total_jour = somme(cout_essence de tous les trajets)`
4. `heure_fin = heure_debut + somme(duree_trajet_min + duree_chantier_min) sur tous les trajets`
5. `fuel_price_cache` rafraîchi via appel API gouv (data.economie.gouv.fr) à la demande
   si `date_maj` > 24h, moyenne glissante sur relevés des 7 derniers jours.

## UX Flow
1. Login (Supabase Auth UI hébergée ou composant custom) — Google / Facebook / email
2. Si aucun `vehicle_profiles` → onboarding modal obligatoire (conso + carburant)
3. Dashboard "Tournée du jour": heure début éditable, liste trajets (cards, drag-reorder
   via dnd-kit), bouton "+ Ajouter trajet" → modal (autocomplete adresse via Nominatim,
   durée chantier en minutes)
4. Panneau récap (sticky, animé — Framer Motion, compteurs numériques qui s'incrémentent) :
   coût par trajet inline sur chaque card, coût total jour + heure fin en gros dans le panneau
5. Thème dark, accents gradient, micro-interactions sur ajout/suppression/reorder

## Error handling
- Adresse non géocodable (Nominatim 0 résultat) → message inline, pas de crash calc
- OSRM indisponible → fallback distance à vol d'oiseau (haversine) + indicateur "estimation approx."
- API gouv carburant indisponible → garder dernier prix en cache avec badge "prix non à jour"

## Testing
- Backend: pytest — calcul coût/distance/heure fin, mocks OSRM + API gouv, cas erreurs ci-dessus
- Frontend: vérification manuelle via `run` skill (pas d'E2E en V1)

## Stack récap
| Composant | Choix |
|---|---|
| Frontend | Next.js + Tailwind + Framer Motion |
| Backend | FastAPI (Python, uv) |
| Auth + DB | Supabase Cloud |
| Routing/Géocodage | OSRM + Nominatim (Docker, self-hosted) |
| Prix carburant | API prix-carburants.gouv.fr |
| Infra | docker-compose + uv |
