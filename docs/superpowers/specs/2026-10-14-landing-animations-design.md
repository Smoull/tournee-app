# Landing Bouclé.tech : animations et démo vivante (design)

Complète `2026-10-12-landing-validation-design.md` (phase 1 livrée). Textes, DA (4 couleurs,
Manrope seule, logo), formulaire et API inchangés.

## Objectif
La v1 est propre mais banale. Rendre la page vendeuse et mémorable : en moins de 5 secondes,
un pro en tournée sur son téléphone **voit** ce que fait Bouclé et se dit « ce n'est pas un site
comme les autres ».

Contraintes reprises : cible peu numérique, mobile, souvent dehors ; le spectacle sert la
compréhension et ne gêne jamais la lecture ; pas de CDN ; `prefers-reduced-motion` respecté ;
tout le texte reste dans le HTML (lisible sans JS, indexable).

## Ce qui se passe à l'écran

### 1. Hero : démo vivante (un scénario par métier)
Sous le H1 : mini-carte stylisée (rues abstraites en `principale` à faible opacité), 5 arrêts
évidés comme le logo, chacun avec son heure ; la route se trace.

Séquence (≈ 4 s, jouée une fois à chaque entrée de la démo à l'écran puis arrêt sur l'état final,
pas de boucle infinie : WCAG 2.2.2) :
1. 0 → 1,2 s : la route se trace, les arrêts apparaissent.
2. 1,5 s : l'imprévu arrive (icône Phosphor + étiquette courte) sur l'arrêt concerné.
3. 2,5 s : retrait = l'arrêt se grise puis disparaît ; ajout = un nouvel arrêt apparaît.
   La route se redessine vers son nouveau tracé (l'ancienne route s'estompe pendant que la nouvelle se trace : les deux tracés n'ont pas le même nombre de points, un morphing n'est pas possible), les heures suivantes changent.
4. 4 s : une bulle SMS glisse depuis le bas avec la nouvelle heure.
5. Fin : état final affiché (le halo du CTA pulse 2 fois, puis s'arrête).

Bouton « Rejouer » pour relancer à la demande.

| Variante | Type | Imprévu | Texte SMS |
|---|---|---|---|
| `/` générique | ajout (position 2) | « Un client ajoute un passage » | Bonjour, votre passage est décalé à {heure}. Bouclé.tech |
| `/laveur-vitres` | retrait (1er arrêt, 7h00) | « Annulation à 7h » | Bonjour, nous pouvons passer plus tôt : {heure}. Bouclé.tech |
| `/infirmier` | retrait (position 2) | « Patient absent » | Bonjour, mon passage chez vous est avancé à {heure}. Bouclé.tech |
| `/services-domicile` | ajout (position 1) | « Demande urgente » | Bonjour, votre passage est décalé à {heure}. Bouclé.tech |

Règles horaires : 5 arrêts de départ, premier passage à l'heure de début du scénario, un arrêt
toutes les 45 min. Retrait : les arrêts suivants avancent de 45 min. Ajout : les suivants reculent
de 45 min. `{heure}` = nouvelle heure du **premier arrêt existant dont l'heure change**, au format
`10h30` (sans zéro initial : `7h00`). Aucun nom de client, aucune donnée de santé.

### 2. Arrêts de section
Chaque section (Douleurs, On configure, Vos données, Prix) a un arrêt évidé qui se remplit à
l'entrée de la section. Le CTA du formulaire est l'arrivée ambre avec halo. La ligne qui
serpentait dans la marge a été retirée (jugée parasite, 2026-10-14).

### 3. Petits moments
- Cartes de douleur : entrée décalée, une icône Phosphor par carte.
- Prix : 49 € se raye, 24,50 € apparaît, « 294 € HT économisés » défile de 0 à 294.
- Compteur : 10 pastilles, les places prises pleines.
- Page merci : la route se boucle, puis « C'est bouclé. ».

### Garde-fous
- `prefers-reduced-motion` ou JS absent : tout est affiché à l'état final, sans mouvement.
- Les états cachés de départ sont posés par le JS uniquement (jamais de contenu invisible sans JS).
- Aucune animation ne recouvre le texte ou le CTA.

## Architecture

### Python (logique, testée par pytest)
- `app/demo/scenario.py` : `DemoStop(heure: time, x: float, y: float)`,
  `Incident(kind: Literal["retrait", "ajout"], position: int, label: str, icon: str)`,
  `DemoScenario(debut: time, positions: tuple[(x, y), ...], incident: Incident, ajout_xy: (x, y) | None, sms: str)`.
- `app/demo/route_geometry.py` : fonctions pures :
  - `stops_before(scenario) -> tuple[DemoStop, ...]` et `stops_after(scenario) -> tuple[DemoStop, ...]`
  - `route_path(stops) -> str` : chemin SVG arrondi passant par tous les arrêts
  - `sms_text(scenario) -> str` : SMS avec `{heure}` remplacée
- `content/<metier>.py` : chaque `Variant` reçoit `demo: DemoScenario`. Les textes de démo et
  SMS sont couverts par les garde-fous existants (vouvoiement, pas de tiret cadratin, pas de
  mot de santé côté infirmier).
- `app/icons.py` : `icon(name: str) -> Markup` insère le SVG Phosphor stocké localement.
  Icône inconnue = erreur explicite (fail fast).

### Gabarits
- `templates/_demo.html` : démo rendue **à l'état final** côté serveur + données d'animation
  (arrêts avant/après, chemins, SMS) dans des attributs `data-*` sur chaque arrêt (pas de bloc JSON).
- Fil de la route : SVG décoratif étiré (`preserveAspectRatio="none"`,
  `vector-effect: non-scaling-stroke`) + un marqueur d'arrêt par section.

### JS (joue, ne calcule pas)
- `static/js/vendor/motion.js` : Motion (MIT), build UMD global `Motion`, version figée,
  téléchargée une fois par `tools/vendor_assets.py` depuis le registre npm et vérifiée par l'empreinte
  `integrity` (sha512) publiée par le registre. Licence copiée à côté.
- `static/js/demo.js` : séquence de la démo, pause hors écran (`inView`), bouton Rejouer.
- `static/js/route-scroll.js` : fil au défilement (`scroll`), arrêts, prix, compteur.
- Budget : ≤ 60 Ko de JS transférés (gzip) au total ; Motion seul pèse 49 Ko gzip, chargé en `defer`.

### Icônes Phosphor (MIT)
Style `regular`, SVG stockés dans `app/static_src/icons/` (+ `LICENSE`), téléchargés par
`tools/vendor_assets.py` depuis le paquet npm `@phosphor-icons/core` (version figée, empreinte vérifiée).
Liste fermée : `x-circle`, `user-minus`, `plus-circle`, `lightning`, `chat-text`, `printer`,
`hand-heart`, `shield-check`, `clock-countdown`, `calendar-check`, `map-pin`, `arrow-counter-clockwise`.
Couleur via `currentColor` (palette uniquement).

## Tests
pytest :
- géométrie : la route part du 1er arrêt et finit au dernier ; retrait : l'arrêt disparaît et les
  suivants avancent de 45 min ; ajout : un arrêt de plus et les suivants reculent de 45 min ;
  le SMS contient la nouvelle heure du premier arrêt changé, au format `10h30`.
- chaque variante a un scénario valide (position dans les bornes, icône existante, SMS avec `{heure}`).
- icônes : chaque icône de la liste existe, utilise `currentColor` ; icône inconnue → erreur.
- rendu : la page contient la démo à l'état final, le JSON de démo est valide, `demo.js`,
  `route-scroll.js` et `motion.js` sont référencés, aucun script inline exécutable.

Vérification manuelle : captures en temps réel (Firefox headless + page enveloppe qui retarde la fin du chargement ; le temps virtuel de Chrome headless ne fait pas avancer les animations JS) à 0 s, 2 s, 5 s et après défilement,
desktop et 375 px, avec et sans `prefers-reduced-motion` ; puis test humain au clic.

## Hors scope
Vraie carte (tuiles, API), son, vidéo, 3D, A/B test des animations.
