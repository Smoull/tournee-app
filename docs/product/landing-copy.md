# Textes de la landing Bouclé.tech (premier jet)

Méthode FUOM : **Utilité → Faisabilité → Morale → Opportunité → Formulaire**.
Règles : vouvoiement, pas de tiret cadratin, prix HT, phrases courtes (cible peu numérique, mobile).
`{places}` = places en accès anticipé restantes (N à définir par le marketing).

Les blocs **Faisabilité, Morale, Opportunité, Formulaire** sont communs aux 4 variantes ; seuls
le **hero** et l'**Utilité** (3 douleurs) changent par métier.

---

## Variante `/` : générique "pros en tournée"

**Hero**
- H1 : **Un imprévu à 7h, et toute la journée déraille ?**
- Sous-titre : Bouclé recalcule votre tournée et prévient vos clients par SMS. Vous, vous conduisez.
- CTA : **Je réserve ma place**
- Sous le CTA : 24,50 € HT/mois à vie pour les {places} premiers.

**Utilité : 3 douleurs → solution**
1. **Un client annule, un autre ajoute un passage.** → Votre tournée se réorganise en un geste. Les clients concernés reçoivent leur nouvel horaire par SMS.
2. **Des kilomètres en trop, sans s'en rendre compte.** → Bouclé ordonne vos arrêts et chiffre le coût de chaque journée : carburant, temps, rentabilité.
3. **Le planning de la semaine tient dans votre tête.** → Il tient sur une page : imprimable chaque matin, partageable avec vos collègues.

---

## Variante `/laveur-vitres`

**Hero**
- H1 : **Un client annule à 7h ?**
- Sous-titre : Votre tournée se recalcule, vos clients sont prévenus par SMS. Vous gardez votre matinée.
- CTA : **Je réserve ma place**

**Utilité**
1. **La pluie décale toute la journée.** → Reportez en un geste : Bouclé repropose les créneaux et prévient chaque client.
2. **Les passages tous les 2 mois, il faut s'en souvenir.** → Les clients récurrents reviennent tout seuls dans votre planning, au bon rythme.
3. **Porte fermée, client absent, trajet pour rien.** → La veille, un SMS confirme le passage. Le client absent se signale avant, pas après.

---

## Variante `/infirmier`

> Aucune donnée de santé collectée ni évoquée (cf. spec, HDS). On parle de tournée, d'horaires et de trajets, jamais de soins ou de pathologies.

**Hero**
- H1 : **Un passage ajouté en dernière minute, et toute la tournée glisse ?**
- Sous-titre : Bouclé réorganise votre tournée en respectant vos horaires fixes, et prévient vos patients de l'heure de passage.
- CTA : **Je réserve ma place**

**Utilité**
1. **Des passages à heure fixe à tenir coûte que coûte.** → Vous les verrouillez : Bouclé organise le reste de la tournée autour.
2. **Un patient absent ou un remplacement imprévu.** → La tournée se recalcule, les patients suivants reçoivent leur nouvel horaire par SMS.
3. **Les kilomètres du cabinet, mal répartis.** → Une vue claire des trajets de la journée, imprimable, partageable avec vos collègues ou votre remplaçante.

---

## Variante `/services-domicile` (aide à domicile, jardinier, ramoneur)

**Hero**
- H1 : **Trois clients à caser, un seul après-midi ?**
- Sous-titre : Bouclé trouve le bon ordre de passage et prévient vos clients par SMS. Vous arrivez à l'heure, sans courir.
- CTA : **Je réserve ma place**

**Utilité**
1. **Les demandes arrivent en vrac, au téléphone.** → Ajoutez-les en quelques secondes : Bouclé leur trouve une place dans la semaine.
2. **Les pics de saison (taille, ramonage, entretien) débordent.** → Bouclé répartit les passages sur plusieurs semaines, sans oublier personne.
3. **Plusieurs intervenants, qui va où ?** → Chacun reçoit sa tournée, vous gardez la vue d'ensemble.

---

## Blocs communs

### Faisabilité : "Je vais y arriver ?"
- H2 (Manrope) : **On configure tout pour vous**
- **Prise en main en 5 minutes.** On importe vos clients avec vous, au téléphone si besoin.
- **Votre tournée sur papier.** Un PDF clair, imprimable chaque matin.
- **Vous gardez la main.** Bouclé propose, vous validez ou vous modifiez. Toujours.

### Morale : "Je peux leur faire confiance ?"
- H2 : **Vos données restent les vôtres**
- **Hébergées en France.** Jamais revendues, jamais partagées. *(à garantir : région Supabase Paris)*
- **Vos clients respectés.** Prévenus avant, jamais surpris par un retard.
- **Du temps rendu.** Moins de trajets et de coups de fil, plus de soirées pour vous et vos proches.

### Opportunité : "Pourquoi maintenant ?"
- H2 : **Accès anticipé : le prix des premiers, à vie**
- Prix barré **49 € HT/mois** → **24,50 € HT/mois à vie**
- **-24,50 € HT/mois à vie, soit 294 € HT économisés chaque année.**
- Compteur : **Plus que {places} places en accès anticipé.**
- Coût de l'attente : Après les {places} premières places, le tarif passe à 49 € HT/mois. Sans engagement : vous réservez votre place, vous ne payez rien aujourd'hui.

### Formulaire
- H2 : **Réservez votre place**
- Intro : 30 secondes. Aucun paiement aujourd'hui.
- Champs :
  - Votre métier
  - Votre équipe : Seul(e) / 2 à 5 / 6 et plus
  - Ce qui vous pèse le plus : Les imprévus / La rentabilité / Le planning / La coordination / Autre chose
  - Votre email
  - Votre téléphone
  - ☐ J'accepte un appel de 15 minutes pour parler de ma tournée
  - ☐ J'accepte que Bouclé.tech utilise ces informations pour me recontacter au sujet de l'accès anticipé ([politique de confidentialité](/confidentialite))
- Bouton : **Je réserve ma place**
- Erreurs :
  - Champ invalide : message sous le champ (ex. "Ce numéro ne semble pas complet.")
  - Déjà inscrit (409) : **Vous êtes déjà sur la liste. À très vite !**
  - Indisponible (503) : **Une erreur est survenue, réessayez dans un instant.** Ou écrivez-nous : {contact_email}

### Page merci
- H1 : **C'est bouclé.**
- Votre place en accès anticipé est réservée : 24,50 € HT/mois à vie.
- On vous recontacte très vite. Pour aller plus vite, réservez un appel de 15 minutes : **[Choisir un créneau]** (Cal.com)

### Pied de page
Bouclé.tech · Votre tournée, sans détour. · Mentions légales · Confidentialité · Se désinscrire
