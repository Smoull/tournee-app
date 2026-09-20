# Tournée App — V1 Design (sans optimisation)

## Contexte
Webapp SaaS pour artisans/pros terrain : gérer tournée du jour (trajets clients),
calculer coût essence + heure de fin estimée. Design haut de gamme, animé.
Blog SEO traité en spec séparée (hors scope V1).

## Objectifs V1
- Profil véhicule (conso + carburant), une fois
- Prix carburant auto (moyenne glissante 7j, API gouv) + changement manuelle si besoin
- Ajout trajets du jour un par un, adresse + durée chantier, ordre manuel (drag)
- Calcul: coût essence/trajet, coût total jour, heure de fin estimée
- Auth SSO Google/Facebook + email/password
- UI "mega pro", animée (SaaS-grade)

Hors scope V1: optimisation d'itinéraire, multi-véhicules simultanés, blog.

## Architecture

```
[Next.js frontend] --REST--> [FastAPI backend] --> [Mapbox Directions/Geocoding API]
        |                          |
        |                          --> [API gouv prix-carburants]
        |                          --> [Supabase Postgres via service_role]
        --> [Supabase Auth uniquement (JWT)]
```

**Décision (override règle "open source only"):** Mapbox choisi plutôt qu'OSRM/Nominatim
self-host pour V1 — build/maintenance du graphe routier OSRM jugés disproportionnés pour le
volume V1 (quelques trajets/jour). Migration vers OSRM reste possible en V2 si coût Mapbox
ou volume le justifient ; le calcul de coût (§ Logique de calcul) est agnostique du provider.

- **Frontend**: Next.js (App Router, TS), Tailwind, Framer Motion. Consomme **uniquement**
  Supabase Auth (session JWT) pour le login. Aucune lecture/écriture directe des tables
  métier — tout passe par FastAPI (chemin de données unique, plus simple à sécuriser/tester).
- **Backend**: FastAPI (Python, géré par `uv`). Seul composant à lire/écrire le Postgres
  Supabase (via `service_role` key). Valide le JWT Supabase reçu du frontend sur chaque
  requête et vérifie explicitement `user_id` en code (RLS n'est PAS le seul rempart :
  `service_role` bypass RLS, donc l'isolation par utilisateur est appliquée dans les
  queries FastAPI, pas seulement en DB). Endpoints: vehicle profile CRUD, tournée CRUD,
  calc trajet (géocodage + distance + coût), refresh prix carburant.
- **Auth + DB**: Supabase Cloud (Postgres managé + Auth SSO Google/Facebook/email).
- **Routing/Géocodage**: Mapbox Geocoding API (autocomplete + validation adresse) +
  Mapbox Directions API (distance/durée), appelés côté backend FastAPI (clé API jamais
  exposée au frontend).
- **Infra**: `docker-compose.yml` (api uniquement — plus de service routing à héberger).
  Frontend déployé séparément (Vercel ou même compose). `uv` pour gestion deps Python backend.

## Data model (Postgres, schéma `public`, RLS activé par user_id)

```sql
vehicle_profiles (
  id uuid pk, user_id uuid fk auth.users, nom text,
  conso_l_100km numeric, type_carburant text,  -- gazole|sp95|sp98|e10|e85|gplc
  adresse_depart text, lat_depart numeric, lon_depart numeric  -- géocodé via Nominatim
)

fuel_price_cache (
  -- clé composite type+département: prix carburant varie fort par zone en France,
  -- une moyenne nationale seule serait trop imprécise
  type_carburant text, departement text, prix_moyen_7j numeric, date_maj timestamptz,
  primary key (type_carburant, departement)
)

tournees (
  id uuid pk, user_id uuid fk, date date, heure_debut time, statut text
)

clients (
  -- préparé en V1 (FK nullable) pour éviter migration lourde en V2 (carnet clients)
  id uuid pk, user_id uuid fk, nom text, adresse text, lat numeric, lon numeric
)

trajets (
  id uuid pk, tournee_id uuid fk, client_id uuid fk clients null,
  ordre int, adresse text, lat numeric, lon numeric,  -- géocodé via Nominatim (voir Validation adresse)
  duree_chantier_min int,
  distance_km numeric,      -- calculé (OSRM depuis point précédent, ou départ véhicule)
  duree_trajet_min numeric, -- calculé (OSRM)
  cout_essence numeric      -- calculé: distance_km * (conso/100) * prix_carburant
)
```

`clients` non exposé dans l'UI en V1 (pas de carnet visible) — table présente uniquement pour
absorber la FK sans migration en V2. `trajets.adresse/lat/lon` restent la source de vérité en V1
même si `client_id` est renseigné plus tard.

## Logique de calcul
1. Trigger: ajout/reorder d'un trajet → backend recalcule distance/durée via Mapbox
   Directions entre trajet précédent (ou point de départ) et ce trajet. Sur un reorder,
   le frontend **debounce** l'appel (attend fin du drag, ~500ms) et n'envoie qu'un seul
   recalcul batch pour les trajets dont l'ordre a changé (pas un appel par étape intermédiaire).
2. `departement` du calcul carburant dérivé du `adresse_depart` du véhicule (code postal → dept).
3. `cout_essence = distance_km * (conso_l_100km / 100) * prix_moyen_7j` (prix du département du véhicule)
4. `cout_total_jour = somme(cout_essence de tous les trajets)`
5. `heure_fin = heure_debut + somme(duree_trajet_min + duree_chantier_min) sur tous les trajets`
6. `fuel_price_cache` rafraîchi via appel API gouv (data.economie.gouv.fr) à la demande
   si `date_maj` > 24h pour ce département, moyenne glissante sur relevés des 7 derniers jours.

## UX Flow
1. Login (Supabase Auth UI hébergée ou composant custom) — Google / Facebook / email
2. Si aucun `vehicle_profiles` → onboarding modal obligatoire (conso + carburant)
3. Dashboard "Tournée du jour": heure début éditable, liste trajets (cards, drag-reorder
   via dnd-kit), bouton "+ Ajouter trajet" → modal (autocomplete adresse via Nominatim,
   durée chantier en minutes)
4. Panneau récap (sticky, animé — Framer Motion, compteurs numériques qui s'incrémentent) :
   coût par trajet inline sur chaque card, coût total jour + heure fin en gros dans le panneau
5. Thème dark, accents gradient, micro-interactions sur ajout/suppression/reorder

## Validation adresse (départ + trajets)
- Autocomplete Mapbox Geocoding au champ adresse : user sélectionne une suggestion →
  lat/lon stockés directement, pas de re-géocodage.
- Si texte libre soumis sans sélection → géocodage backend au submit ; 0 résultat ou score
  de confiance bas → erreur inline "adresse introuvable", sauvegarde bloquée.
- Point de départ (adresse véhicule) : même validation, saisi une fois dans le profil véhicule.

## Évolution V2 (hors scope V1, architecture compatible sans refonte)
- **Carnet clients** : table `clients` déjà présente (V1), exposée en UI V2 (sélection au lieu
  de retaper l'adresse)
- **Créneaux fixes** : ajout `clients.creneau_debut/fin` (nouvelle colonne, pas de migration structurelle)
- **Optimisation ordre** : nouvel endpoint FastAPI `/tournees/{id}/optimize`, utilise Mapbox
  Optimization API (même provider que V1) ou migration OSRM Trip Service si coût/volume
  le justifie à ce stade
- **Réordonnancement manuel post-optim + recalcul live** : réutilise la logique de calcul V1
- **Export Google Agenda** : intégration Google Calendar API, service indépendant

## Error handling
- Adresse non géocodable (Mapbox 0 résultat) → message inline, pas de crash calc
- Mapbox indisponible/quota dépassé → fallback distance à vol d'oiseau (haversine) + indicateur "estimation approx."
- API gouv carburant indisponible → garder dernier prix en cache (par département) avec badge "prix non à jour"

## Testing
- Backend: pytest — calcul coût/distance/heure fin, mocks Mapbox + API gouv, cas erreurs ci-dessus
- Frontend: vérification manuelle via `run` skill (pas d'E2E en V1)

## Analytics (PostHog)
- PostHog Cloud EU (RGPD), pas de self-host V1
- Frontend: `posthog-js` init au layout root Next.js, autocapture pageviews +
  events custom (`vehicle_profile_created`, `trajet_ajoute`, `tournee_calculee`, `signup`)
- Backend (optionnel V1, utile si events critiques doivent être fiables côté serveur):
  `posthog-python` dans FastAPI pour events métier (ex: `calc_echoue`)
- Feature flags PostHog disponibles gratuitement si A/B test nécessaire plus tard

## Blog (architecture seulement — scope détaillé en spec séparée)
- Même repo Next.js, route group indépendant `app/(blog)/blog/[slug]`
- Contenu V1: MDX en local (versionné git), migrable vers headless CMS
  (ex: Payload/Strapi self-host) si volume de contenu grandit
- SSG via `generateStaticParams` pour SEO max — aucune dépendance FastAPI/Supabase
- Sitemap.xml + metadata dynamique via Next Metadata API
- Aucun couplage avec l'app métier (routes indépendantes), déploiement commun (même build Next.js)
- Events PostHog blog séparés des events app (`blog_article_vu`, etc.) pour analyse distincte

## Stack récap
| Composant | Choix |
|---|---|
| Frontend | Next.js + Tailwind + Framer Motion |
| Backend | FastAPI (Python, uv) |
| Auth + DB | Supabase Cloud |
| Routing/Géocodage | Mapbox Directions + Geocoding API (override open-source, voir Architecture) |
| Prix carburant | API prix-carburants.gouv.fr |
| Analytics | PostHog Cloud EU |
| Infra | docker-compose + uv |
