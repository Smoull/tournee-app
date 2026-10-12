# Landing de validation — Design ("fake it before make it")

## Contexte
Avant de coder l'app, valider quel métier de tournée a la douleur la plus forte et une
intention d'achat réelle. Landing premium + trafic (société de contenu + direct) + collecte
de contacts qualifiés + appels de découverte. Le plan V1
(`docs/superpowers/plans/2026-09-20-tournee-app-v1.md`) est **gelé** jusqu'au verdict :
la V1 sera re-spécifiée pour le métier gagnant.

Cible : pros en tournée peu à l'aise avec le numérique. Proposition : cœur réutilisable,
champs personnalisés par persona ; aide forte (stats, génération de planning, SMS auto,
PDF, CSV) avec reprise en main humaine.

## Objectif et métrique
**100 contacts qualifiés** en 6 semaines max.
Contact qualifié = métier + taille + douleur n°1 déclarée + accepte un appel de 15 min.

## Protocole de test
- Durée : 6 semaines max, ou arrêt à 100 qualifiés.
- Trafic séparé par UTM : `utm_source=agence` (société de contenu) vs `utm_source=direct`
  (groupes FB métier, appels, bouche-à-oreille) → mesure du ROI de l'agence.
- Mesuré par variante : visites, conversion visite → lead, % qualifiés, douleur n°1 dominante.
- 10-15 appels de 15 min (méthode *Mom Test* : parler de leur passé, pas du produit).
  Une fiche par appel : `docs/product/interviews/AAAA-MM-JJ-<metier>-<n>.md` (aucune donnée
  personnelle réelle dans le repo : prénom anonymisé, pas de téléphone/email).

### Règle de décision
- **Métier gagnant** : meilleur taux de qualifiés, avec ≥ 30 leads sur la variante
  (en dessous, écart non significatif).
- **Go dev** : un métier ≥ 30 qualifiés ET ≥ 3 "je paierais 49 € HT/mois" en appel →
  nouvelle spec V1 ciblée sur ce métier, remplace la spec V1 actuelle.
- **Pivot** : < 30 qualifiés au total après 6 semaines → revoir douleur ou cible, pas le design.
- Repère conversion visite → lead : 1-3 % faible, > 5 % bon.

## Variantes
| Route | Métier |
|---|---|
| `/` | Générique "pros en tournée" (métier choisi dans le formulaire) |
| `/laveur-vitres` | Laveur de vitres |
| `/infirmier` | Infirmier libéral |
| `/services-domicile` | Aide à domicile / jardinier / ramoneur |

Infirmier : la landing ne collecte aucune donnée de santé. Si ce métier gagne, le produit
devra traiter la question HDS (hébergement données de santé) avant tout dev.

## Persuasion — FUOM
Ordre de la page : **Utilité → Faisabilité → Morale → Opportunité → Formulaire**.

| Pilier | Objection traitée | Contenu |
|---|---|---|
| Utilité | "Ça règle mon problème ?" | Hero = douleur n°1 du métier (ex. laveur : "Un client annule à 7h ? Ta tournée se recalcule, tes clients sont prévenus par SMS."), puis 3 douleurs → solution |
| Faisabilité | "Je vais y arriver ?" (objection n°1 de la cible) | "On configure pour vous", prise en main 5 min, PDF imprimable, l'humain garde la main |
| Morale | "Je peux leur faire confiance ?" | Données hébergées en France, pas de revente, temps rendu (famille, patients), clients respectés car prévenus |
| Opportunité | "Pourquoi maintenant ?" | **49 € HT/mois** (prix affiché HT sur toutes les variantes), early access **-50 % à vie (24,50 € HT/mois) pour les 100 premiers**, compteur de places, coût de l'attente |

Contenu par métier dans `landing/content/<metier>.ts` (un fichier = une variante).

## Design
- Skill `design-taste-frontend` (taste-skill, MIT) :
  `npx skills add https://github.com/Leonxlnx/taste-skill --skill "design-taste-frontend"`.
- Animations avec **Motion** (MIT) à la place de GSAP (licence non open source).
- Règle taste-skill reprise : pas de tiret cadratin dans les textes UI.
- Lisibilité prioritaire pour la cible : gros CTA, contraste WCAG AA, mobile first
  (trafic majoritairement mobile depuis réseaux sociaux).

## Formulaire
Un écran, 5 champs max.

| Champ | Type | Règle |
|---|---|---|
| `metier` | select, pré-rempli par variante | requis |
| `taille` | `solo` / `2-5` / `6+` | requis |
| `douleur` | `imprevus` / `rentabilite` / `planning` / `coordination` / `autre` | requis |
| `email` | email | requis, unique |
| `phone` | tel (format FR) | requis |
| `accepte_appel` | checkbox | optionnel |
| `consentement_rgpd` | checkbox | requis, sinon refus |
| `website` | honeypot invisible | doit être vide, sinon 400 et rien de stocké |

Après envoi : page merci (confirmation early access) + lien Cal.com pour réserver l'appel.

## Données
Table Supabase `leads` :
`id`, `created_at`, `metier`, `taille`, `douleur`, `email` (unique), `phone`,
`accepte_appel`, `utm_source`, `utm_campaign`, `variante`.

RLS : rôle `anon` = **INSERT uniquement** sur `leads` (aucun SELECT/UPDATE/DELETE).
La clé `service_role` n'est jamais utilisée par la landing.

Rétention : suppression des leads sans suite après 12 mois (cf. politique de confidentialité).

## Architecture
```
[Visiteur] --HTTPS--> [Traefik (Let's Encrypt, rate limit)] --> [Next.js landing]
                                                                    |
                                                        POST /api/leads (server)
                                                                    |
                                                      [Supabase Cloud: leads]
[Navigateur] --> [PostHog Cloud EU, mode sans cookie]
[Page merci]  --> [Cal.com]
```

- `landing/` à la racine : Next.js (SSG pour les pages, route handler `/api/leads`),
  Tailwind, Motion. Pas de FastAPI (une seule insertion, YAGNI ; FastAPI arrive avec l'app).
- Responsabilités :
  - `content/<metier>.ts` : textes FUOM d'une variante
  - `lib/leadSchema.ts` : validation des champs (seul endroit si le formulaire change)
  - `lib/leadRepository.ts` : insertion Supabase (seul endroit si le stockage change)
  - `app/api/leads/route.ts` : orchestration HTTP (valide → insère → code retour)
- Secrets : `.env.local` (gitignoré) en local — `SUPABASE_URL`, `SUPABASE_ANON_KEY`,
  `POSTHOG_KEY` ; variables d'env du container en prod. Jamais en dur.

## Hébergement
OVH VPS, Docker Compose (Traefik + landing). TLS Let's Encrypt (ACME via Traefik),
redirection HTTP → HTTPS, rate limit Traefik sur `/api/leads`. Domaine dédié.

## Analytics
PostHog Cloud EU, **mode sans cookie** (pas de bannière, cible non perdue).
Events : `landing_vue`, `form_commence`, `lead_envoye`, propriétés `variante`, `utm_source`,
`utm_campaign`.

## Gestion d'erreur (fail fast)
| Cas | Réponse API | UI |
|---|---|---|
| Champ invalide / consentement absent | 400 + champ fautif | erreur sous le champ |
| Email déjà inscrit | 409 | "Vous êtes déjà sur la liste" |
| Honeypot rempli | 400 | rien de stocké |
| Supabase indisponible | 503 | "Erreur, réessayez" + email de contact en clair |

Pas de file d'attente locale, pas de faux succès, pas de stockage de secours.

## Tests (TDD)
Vitest :
- `leadSchema` : chaque champ requis, format email/tel, consentement obligatoire, honeypot
- route `/api/leads` (repository mocké) : 201 nominal, 400, 409 doublon, 503 Supabase down
- mapping variante → contenu (chaque route a un contenu FUOM complet)

Pas d'E2E. Vérification manuelle navigateur (skill `run`) desktop + mobile avant mise en ligne.

## Légal (`docs/legal/`)
Mentions légales, politique de confidentialité (finalité, durée 12 mois, droit d'accès et
suppression), lien de désinscription.

## Hors scope
L'app elle-même, A/B test au sein d'une variante, blog, emailing automatisé (relance
manuelle), stratégie marketing et contenus d'acquisition (gérés par la société de contenu).
