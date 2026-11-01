# Routine quotidienne : 3 vidéos par jour

Ce fichier est le mode d'emploi de la routine Claude qui tourne chaque matin.
Objectif : créer 3 épisodes d'environ 1 min 30 et les programmer dans Metricool à
**10:00, 12:00 et 18:00 (Europe/Paris)** le jour même, sans intervention humaine.

## Contexte fixe

- Metricool : brand `blogId` = `7755029`, fuseau `Europe/Paris`.
- Les vidéos sont servies à Metricool depuis la branche **`media`** de ce dépôt :
  `https://raw.githubusercontent.com/diego029929/vid-os-/media/<fichier>.mp4`.
  Metricool copie le fichier chez lui au moment de la programmation, donc à
  chaque exécution les vidéos précédentes sont **supprimées** de la branche
  `media` avant d'ajouter les nouvelles (libère de l'espace).
- On ne commite **jamais** de MP4 sur `main`.
- Moteur : `python3 engine/render2.py episodes/epNN.json /chemin/sortie.mp4`
  (style 2, depuis le 02/11 ; l'ancien `engine/render.py` ne sert plus que
  pour les anciens épisodes).
- Épisodes = fichiers JSON dans `episodes/`. Lire `episodes/essai-style2.json`
  comme exemple complet du format style 2 (décors, cadrages, caméra, texte,
  `*mots rouges*`, choix A/B, `record` + `rewind`, bruitages).
- État de la série : `series/state.json`. Plan de la série : fichier indiqué
  dans `series_file`.

## Étapes

0. Préparer la voix off : `pip install -q chatterbox-tts`. Voix validée par
   Fio le 01/11 (essai « V1 ») : Chatterbox, timbre
   `assets/ref/ref-pierre-moyen.wav`, exagération 0.6, **30 % plus rapide,
   sans effet radio**, pauses raccourcies. Le moteur `engine/render2.py`
   règle tout seul la vitesse (1.3) et l'effet (« leger ») : ne pas changer
   sans Fio. Le modèle se télécharge depuis huggingface.co au premier rendu.
   Si l'installation ou le téléchargement échoue, NE PAS publier : s'arrêter
   et le signaler.

1. `getBrandSettings` (Metricool) : noter les réseaux reliés. TikTok toujours ;
   ajouter Instagram (type `REEL`) seulement s'il apparaît dans `networksData`.
1b. **Analyser les résultats et adapter** (demande de Fio : améliorer les
   vidéos selon les stats).
   - Métriques (`getAnalyticsDataByMetrics`, 14 derniers jours) :
     TikTok `TKPO02, TKPO05, TKPO06, TKPO07, TKPO08, TKPO09, TKPO10,
     TKPO11, TKPO13, TKPO15, TKPO16` ; Instagram Reels `IGRE02, IGRE03,
     IGRE23, IGRE11, IGRE10, IGRE07, IGRE21, IGRE12, IGRE24, IGRE27,
     IGRE28`. Metricool met 24 à 48 h à remonter une vidéo TikTok : ne
     juger une vidéo qu'après 48 h.
   - Rapprocher chaque ligne d'un épisode (date/heure + légende) et remplir
     le tableau de `series/insights.md` : vues, likes, commentaires,
     partages, taux de vue complète / temps moyen si dispo, et pour
     Instagram vues, rétention, partages, enregistrements.
   - **Score** de chaque vidéo = vues × (1 + 5 × (commentaires + partages)
     / vues). Comparer à la médiane des vidéos de la série.
   - **Test du jour** : chaque jour, les 3 vidéos testent UNE seule
     variable à la fois (ex. type d'accroche : question / phrase choc /
     « tu as 3 secondes » ; décor d'ouverture ; longueur 75 vs 90 s ;
     légende courte vs longue). Noter dans `insights.md` la variable
     testée et la version utilisée par chaque vidéo.
   - **Règles de décision** (sur au moins 3 vidéos jugées) :
     - une version dont le score dépasse la médiane de +30 % sur 2 tests
       devient la règle par défaut (l'écrire dans « Règles actives ») ;
     - si le taux de vue complète < 20 % ou le temps moyen < 40 % de la
       durée : raccourcir de 10 s et accélérer les 10 premières secondes ;
     - si le temps moyen > 70 % de la durée : on peut allonger de 10 s ;
     - si les commentaires sont faibles (< 1 % des vues) : rendre le
       dilemme final plus clivant et le poser en début ET en fin de vidéo ;
     - si un épisode fait < 50 % de la médiane : noter pourquoi (accroche,
       sujet) et éviter ce type le lendemain.
   - Toujours appliquer les « Règles actives » de `insights.md` aux
     épisodes du jour, et écrire en une ligne ce qui a changé.
2. Lire `series/state.json` et le plan de la série. Écrire les 3 prochains
   épisodes (`episodes/epNN.json`, NN = numéro global sur 2 chiffres ou plus).
   **Style 2 obligatoire depuis le 02/11** (demande de Fio, d'après une vidéo
   de référence : gros plans, rythme rapide, sous-titres mot par mot) : mettre
   `"style": 2` et suivre le format de `episodes/essai-style2.json` (voir aussi
   l'en-tête de `engine/render2.py`) :
   - **plans très courts** : une phrase de 3 à 8 mots par plan, qui se lit
     en 1 à 2,5 s. Viser **45 à 55 plans** pour 85-95 s. Pas de `dur` sauf
     sur les plans de choix (compte à rebours : `"dur": 3.2`) ;
   - **cadrage TikTok** : changer de cadrage à CHAQUE plan, jamais deux fois
     le même d'affilée. Gros plan visage (`"pose": "face"`, `"head": [0.5,
     0.36, 0.3]`), vue de dos (`"pose": "back"`, `"head": [0.5, 0.5, 0.2]`),
     plan large debout (`"pose": "stand"`, `"head": [0.5, 0.42, 0.14]`),
     assis (`"pose": "sit"`), ou objet seul (radio, porte...). Les têtes
     restent au centre (u entre 0.4 et 0.6, v entre 0.3 et 0.55) : la
     colonne de droite et le bas de l'écran sont couverts par TikTok. Le
     moteur place lui-même sous-titres, cartes A/B et horloge dans la zone
     sûre ; sur les plans de choix mettre `"text_y": 0.2` ;
   - mouvement de caméra différent à chaque plan avec `"cam"` (zoom avant,
     zoom arrière, petit panoramique), `"shake"` pour les moments de peur ;
   - décors du style 2 : `chambre`, `fenetre`, `rue`, `flou` (fond pour les
     gros plans, `"params": {"light": [r,g,b]}` pour la couleur), `porte`,
     `radio` ; les anciens décors restent possibles (recolorés) ;
   - expressions : `normal`, `side` (méfiant), `wide` (choqué, avec
     `"look"`), `scared`, `closed`. Héros : `"hoodie": [235,120,35]`
     (orange) ; autres personnages : autre couleur ;
   - **écrire les heures et nombres pour qu'ils soient bien lus** : le moteur
     lit « 6 H 12 » comme « 6 heures 12 », mais éviter les abréviations
     (écrire « KILOMÈTRES », « NUMÉRO ») ; en cas de doute, mettre la phrase
     à lire dans `"voice"`.
   Règles qui restent valables :
   - durée totale entre **85 et 95 secondes** : chaque plan dure le temps
     de sa réplique, donc la durée dépend surtout du NOMBRE de répliques ;
     le moteur affiche « durée totale » : ajouter ou retirer des plans si on
     sort de la fourchette ;
   - **texte qui a du sens** (demande de Fio, 01/11) : chaque réplique est
     une phrase complète et compréhensible seule ou avec la précédente ;
     jamais de morceau de phrase coupé sur deux plans (pas de « NE REGARDE
     JAMAIS » / « LES SILHOUETTES ») : mettre la phrase entière dans un
     seul plan, ou découper l'affichage avec `"voice"` qui porte la phrase
     complète. Avant le rendu, relire toutes les répliques à la suite comme
     un texte lu à voix haute : l'histoire doit se suivre, sans saut
     logique, sans mot manquant, et chaque règle ou choix doit être clair ;
   - chaque plan avec `text` est lu par la voix off. `"voice": "..."` remplace le texte lu, `"voice": ""`
     coupe la voix sur ce plan (ex. bruitages « TOC TOC ») ;
   - pas de bip à chaque seconde : ne jamais mettre `"tick": true`. Le
     compte à rebours visuel du choix (`countdown`) reste ;
   - accroche forte dans les 2 premières secondes, **jamais de fond blanc
     au début** (demande de Fio : le moteur ouvre le premier plan depuis le
     noir ; ne pas utiliser de décor clair ni de flash blanc dans les 3
     premières secondes) ; si l'épisode précédent
     finissait sur une question, sa réponse se voit dans l'action du début
     (on montre ce que le héros a choisi et ce qui se passe), pas avec une
     phrase sur les commentaires ;
   - **chaque épisode se comprend seul** (demande de Fio, 01/11) : un
     spectateur qui tombe dessus sans avoir vu les autres doit tout capter.
     MAIS **jamais de résumé** (« précédemment... », « dans l'épisode
     d'avant... » : Fio trouve ça nul). À la place, écrire mieux :
     - la situation est posée dans l'accroche, au présent, en une phrase
       concrète (« Imagine. Il est 6 heures. T'as plus d'abri. ») ;
     - chaque personnage, objet ou règle est présenté au moment où il
       apparaît, en quelques mots glissés dans l'action (« la radio de la
       Station 7, celle qui donne les règles », « ta sœur, disparue depuis
       trois jours ») ;
     - jamais de mot qui renvoie à un épisode précédent sans être expliqué
       (« le carnet », « l'inconnu », « la voix ») : dire ce que c'est ;
     - au moment du choix A/B, le spectateur doit savoir exactement ce qui
       est en jeu, sans rien connaître d'avant ;
     - test avant rendu : relire le script comme quelqu'un qui n'a vu
       aucun épisode ; chaque phrase doit se comprendre ;
   - structure : accroche, mise en place, règle, situation, **choix A/B**
     avec compte à rebours, mauvaise option jouée puis `rewind`, bonne
     option, développement (l'histoire avance, nouvelle tension), suspense ;
   - **fin cohérente** : la question finale « A OU B ? RÉPONDS EN
     COMMENTAIRE » doit porter sur un **nouveau dilemme non résolu** (le
     prochain choix de l'histoire, montré avec les cartes A/B sans
     réponse), jamais sur un choix déjà révélé dans la vidéo. Puis
     « ABONNE-TOI POUR LA SUITE » ;
   - commencer `title` par « Partie N · » (N = numéro d'épisode dans la
     série) et mettre « PARTIE N » dans `subtitle` : les séries numérotées
     poussent à regarder les autres épisodes ;
   - remplir `title` (≤ 80 caractères, sert de titre TikTok) et `caption`
     (texte du post avec 4 à 6 hashtags) ;
   - garder la continuité (jour, horloge `clock_start`, personnage).
3. **Fin de série** : si `next_episode_in_series` dépasse
   `series_episode_count`, inventer une nouvelle histoire dans le même style
   (personnages bâton, décors soignés, règles, choix A/B) mais avec un autre
   univers : écrire `series/<slug>.md` (même structure que
   `series/apres-la-fin.md`, **5 ou 6 épisodes**, choix de Fio le 01/11) et mettre à jour `state.json`.
   Il est permis d'ajouter des décors dans `engine/render2.py` (nouvelle
   fonction `scene_xxx` + entrée dans `SCENES`) si l'histoire l'exige.
4. Rendre les 3 vidéos avec `python3 engine/render2.py episodes/epNN.json /tmp/epNN.mp4`
   (le moteur doit afficher `voix off : chatterbox`) dans un dossier temporaire. Un rendu prend 20 à 35 min : le lancer en arrière-plan et attendre la fin. Pour chacune, vérifier
   avec ffprobe la durée (85–95 s) et faire une planche contact
   (`ffmpeg -vf "fps=1/2.5,scale=216:-1,tile=6x4"`) puis la **regarder** :
   texte lisible, rien de coupé, le texte ne cache pas le visage du personnage, pas de mot avec un astérisque visible.
   **Écouter la voix** : si Whisper est disponible (`pip install -q openai-whisper`,
   modèle small, langue fr), transcrire chaque vidéo et comparer au texte :
   un mot répété, bégayé ou incompréhensible = relancer le rendu de cet
   épisode (le moteur retire déjà les répliques au débit anormal, mais pas
   toutes). Écrire les nombres pour qu'ils se lisent bien (le moteur les
   convertit en lettres).
   Corriger et relancer si besoin.
5. Publier les fichiers sur la branche `media` (sans jamais forcer le push) :
   ```
   git fetch --depth 1 origin media && git checkout -B media FETCH_HEAD
   git rm -q --ignore-unmatch *.mp4        # supprime les vidéos déjà envoyées
   cp /chemin/epNN.mp4 .                   # les 3 nouvelles vidéos
   git add -f *.mp4 && git commit -m "Vidéos du JJ/MM"
   git push origin media
   git checkout main
   ```
6. Programmer chaque vidéo avec `createScheduledPost` :
   - `date` / `publicationDate` : aujourd'hui 10:00, 12:00, 18:00 Europe/Paris (choisi par Fio le 01/11 : pics d'audience Metricool à 10h, 12h et 18h)
     (si un horaire est déjà passé, utiliser le prochain horaire libre et
     décaler) ;
   - `autoPublish: true`, `draft: false` ;
   - `media` : l'URL raw de la branche `media` ;
   - `text` : la `caption` ;
   - `tiktokData` : `{"title": <title>, "privacyOption": "PUBLIC_TO_EVERYONE", "isAigc": true}` ;
   - si Instagram : `instagramData` : `{"type": "REEL", "isAiGenerated": true}`.
   Vérifier dans la réponse que `media` pointe vers `static.metricool.com`.
7. Commiter sur `main` les JSON d'épisodes, `series/insights.md`, `series/state.json` (incrémenter
   les compteurs, ajouter les 3 épisodes à `published`) et les éventuels
   changements du moteur, puis `git push origin main`.
7b. Si la programmation Metricool est refusée par la vérification des
   permissions, demander à Fio avec UNE carte de décision (« Publier les 3
   vidéos du jour ? » Oui / Non), puis programmer dès son accord, en
   décalant vers le prochain horaire libre si un créneau est passé.
8. En cas d'échec (rendu, push ou Metricool), ne rien publier de bancal :
   s'arrêter et expliquer le problème dans le compte rendu de la session.
