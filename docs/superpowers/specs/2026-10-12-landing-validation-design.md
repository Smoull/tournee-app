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
Ordre de la page : **Utilité → Rentabilité → Faisabilité → Morale → Opportunité → Formulaire**.
Rentabilité : gain mensuel estimé par métier (essence, temps administratif, no-show) face au prix,
logique dans `app/rentabilite.py`, hypothèses dans `content/<metier>.py`, toujours présenté comme estimation.

| Pilier | Objection traitée | Contenu |
|---|---|---|
| Utilité | "Ça règle mon problème ?" | Hero = douleur n°1 du métier (ex. laveur : "Un client annule à 7h ? Votre tournée se recalcule, vos clients sont prévenus par SMS."), puis 3 douleurs → solution |
| Faisabilité | "Je vais y arriver ?" (objection n°1 de la cible) | "On configure pour vous", prise en main 5 min, PDF imprimable, l'humain garde la main |
| Morale | "Je peux leur faire confiance ?" | Données hébergées en France, pas de revente, temps rendu (famille, patients), clients respectés car prévenus |
| Opportunité | "Pourquoi maintenant ?" | **49 € HT/mois** (prix affiché HT, **sauf `/infirmier` en TTC** : actes infirmiers exonérés de TVA, art. 261-4-1° CGI, ils ne la récupèrent pas → tarif arrondi **59 € TTC**, accès anticipé **29,50 € TTC** (354 € TTC économisés par an) ; coût SMS estimé ≈ 25 € pour 500 SMS/mois), accès anticipé **-50 % à vie : 24,50 € HT/mois pour les N premiers**, affiché "-24,50 € HT/mois à vie, soit 294 € HT économisés chaque année", compteur de places, coût de l'attente |

Nombre de places en accès anticipé N : **à définir** (arbitrage marketing : global vs par variante).
Le compteur reste bloqué tant que N n'est pas fixé.

Contenu par métier dans `landing/content/<metier>.py` (un fichier = une variante).

## Design
- Skill `design-taste-frontend` (taste-skill, MIT) :
  `npx skills add https://github.com/Leonxlnx/taste-skill --skill "design-taste-frontend"`.
- Animations avec **Motion** (MIT), version JS vanilla **auto-hébergée** (fichier copié dans `static/`, pas de CDN : RGPD, pas de npm), à la place
  de GSAP (licence non open source). Le code produit par taste-skill (React) est adapté en Jinja.
- Règle taste-skill reprise : pas de tiret cadratin dans les textes UI.
- **Vouvoiement partout** (accroche, hero, formulaire, SMS d'exemple).
- Lisibilité prioritaire pour la cible : gros CTA, contraste WCAG AA, mobile first
  (trafic majoritairement mobile depuis réseaux sociaux).

## Nom et accroche
- Nom : **Bouclé.tech** ("c'est bouclé" : la tournée est réglée). Wordmark : "Bouclé" + ".tech" à 50 %
  de la taille, même ligne de base (donne du rythme, guide la lecture). Accroche : **"Votre tournée, sans détour."** (route = cohérent avec le logo ; double sens : trajet direct, parler franc)
- Source unique en code : `landing/brand/identity.py`.
- Domaine canonique : **`boucle.tech`** (sans accent), seul domaine écrit dans les liens (SMS, emails, QR).
  **Validé.** `bouclé.tech` (IDN), `boucler.tech`, `boucler.fr` et `tournee.tech` en redirection 301 uniquement
  (protection, fautes de frappe), jamais communiqués.
  Raison : un IDN peut s'afficher en punycode (`xn--boucl-esa.tech`) dans les SMS/emails, ressemble à du
  phishing et nuit à la délivrabilité des SMS, cœur du produit. Libres au 2026-10-14.
  Pour mémoire : `boucle.com` / `boucle.fr` pris. Libres au 2026-10-14 : `cestboucle.fr`, `cestboucle.com`,
  `getboucle.com`, `boucle-pro.fr`. Choix à faire avant la phase 2 (hébergement) ; vérifier INPI
  classes 9 et 42.

## Identité visuelle (DA)
4 couleurs max, **fond clair** : lisible en extérieur sur mobile (reflets), moins "appli tech" pour la cible.
Contrastes vérifiés par `test_palette_meets_wcag_aa`. Tokens Tailwind, nulle part ailleurs.

| Rôle | Couleur | Usage | Contraste vs fond |
|---|---|---|---|
| Neutre fond | `#F4F7F7` (blanc gris clair) | fond de page | - |
| Neutre texte | `#11181C` (ardoise) | texte courant, texte des CTA | 16,6:1 |
| Principale | `#2A7A6B` (vert-bleu profond, "route") | logo, titres, éléments de marque | 4,8:1 |
| Accent | `#C67A10` (ambre cuivré, "panneau routier") | logo (arrivée), CTA, compteur de places, prix de l'accès anticipé uniquement | 3,2:1 (bouton vs fond, WCAG 1.4.11) ; texte `#11181C` sur ambre : 5,3:1 |

Palette proposée, ajustable au choix du logo ; tout changement revérifie WCAG AA.
Variations d'opacité autorisées, aucune 5e teinte.

### Typographie
Une seule famille OFL : **Manrope** (400/600/700/800) pour tout, H1 compris ; la hiérarchie se fait
par la taille et la graisse.
woff2 auto-hébergés, subset latin, pas de CDN (RGPD).

### Logo et assets
- Logo site retenu : **route en S, arrêts évidés façon plan de métro, arrivée ambre + anneau plein**
  (tournée bouclée = tranquillité). Logo future app : même tracé dans une pastille vert-bleu (hors scope landing).
  Le S (parcours simple, tranquillité) et le nom Bouclé (action finie, récurrente) se complètent.
  Source unique : `landing/brand/logo.py`. Régénération : `uv run python -m brand.export`.
- GIF : la route se trace, puis le halo d'arrivée "respire" en boucle.
- Assets dérivés du SVG retenu, dans `landing/static/brand/`, générés par un script
  reproductible (`uv run`, outils open source : `cairosvg`/`Pillow`) :

| Asset | Taille |
|---|---|
| `logo.svg` (+ variante monochrome) | vectoriel |
| `favicon.ico` | 16, 32, 48 |
| `favicon.svg` | vectoriel |
| `apple-touch-icon.png` | 180×180 |
| `icon-192.png`, `icon-512.png` | 192, 512 |
| `og-image.png` (partage réseaux sociaux : logo + nom et accroche en Manrope) | 1200×630 |
| `logo.gif` (route qui se trace puis halo qui respire, en boucle) | 250×250 |
| `logo-halo.gif` (halo seul qui respire, en boucle) | 250×250 |

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

Après envoi : page merci (confirmation de l'accès anticipé) + lien Cal.com pour réserver l'appel.

## Données
Table Supabase `leads` :
`id`, `created_at`, `metier`, `taille`, `douleur`, `email` (unique), `phone`,
`accepte_appel`, `utm_source`, `utm_campaign`, `variante`.

RLS : rôle `anon` = **INSERT uniquement** sur `leads` (aucun SELECT/UPDATE/DELETE).
La clé `service_role` n'est jamais utilisée par la landing.

Rétention : suppression des leads sans suite après 12 mois (cf. politique de confidentialité).

## Architecture
```
[Visiteur] --HTTPS--> [Traefik (Let's Encrypt, rate limit)] --> [FastAPI landing]
                                                                    |
                                                        POST /api/leads (server)
                                                                    |
                                                      [Supabase Cloud: leads]
[Navigateur] --> [PostHog Cloud EU, mode sans cookie]
[Page merci]  --> [Cal.com]
```

- `landing/` à la racine : projet **uv** (tout se lance via `uv run`). FastAPI + Jinja2
  (pages rendues serveur, route `POST /api/leads`), Tailwind via binaire standalone
  (`pytailwindcss`, pas de npm), Motion auto-hébergé. Même stack Python que la future app.
- Responsabilités :
  - `content/<metier>.py` : textes FUOM d'une variante
  - `lead_schema.py` : validation des champs, Pydantic (seul endroit si le formulaire change)
  - `lead_repository.py` : insertion Supabase via HTTP (seul endroit si le stockage change)
  - `routes.py` : orchestration HTTP (valide → insère → code retour)
- Secrets : `landing/secret.toml` (gitignoré, modèle `secret.toml.example`) lu via `tomllib`.
  Clé manquante = erreur au démarrage (fail fast). Jamais en dur.

## Hébergement (phase 2, après finition de la landing)
Hors scope de la phase 1 : on finit la landing en local d'abord.
Cible : repo infra GitLab existant (`~/Documents/infra`, Ansible + Traefik + Let's Encrypt),
nouvelle app `landing` sur le modèle `dsn-api`, variables GitLab `LANDING_*`,
tournee-app migré sur GitLab. CSP propre à la landing (PostHog EU autorisé).

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
pytest (Supabase mocké, aucun appel réseau) :
- `lead_schema` : chaque champ requis, format email/tel, consentement obligatoire, honeypot
- route `/api/leads` (repository mocké) : 201 nominal, 400, 409 doublon, 503 Supabase down
- mapping variante → contenu (chaque route a un contenu FUOM complet)

Pas d'E2E. Vérification manuelle navigateur (skill `run`) desktop + mobile avant mise en ligne.

## Légal (`docs/legal/`)
Mentions légales, politique de confidentialité (finalité, durée 12 mois, droit d'accès et
suppression), lien de désinscription.

## Hors scope
L'app elle-même, A/B test au sein d'une variante, blog, emailing automatisé (relance
manuelle), stratégie marketing et contenus d'acquisition (gérés par la société de contenu).
