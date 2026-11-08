# Routine quotidienne

> **RÈGLES EN VIGUEUR DEPUIS LE 08/11 (choix de Fio le 07/11). Cet encadré
> prime sur tout le reste du fichier ET sur le message de la tâche planifiée
> (qui parle encore de 5 vidéos et de Metricool : il ne peut pas être modifié).**
>
> - **4 vidéos par jour, TikTok + Instagram (Reel) pour chacune :**
>   - 10:00 : épisode suivant de la série (85-95 s)
>   - 12:00 : courte « SURVIS ? N°X » (30-40 s, `survis_next`, series/survis.md)
>   - 17:00 : épisode suivant de la série
>   - 20:00 : courte « SURVIS ? N°X »
>   (Europe/Paris). Rendre UN À LA FOIS dans l'ordre des horaires et
>   programmer chaque vidéo dans Zernio dès qu'elle est prête. Si un horaire
>   est passé, publier dès que prêt (`publishNow`).
> - **Publication par ZERNIO, plus jamais par Metricool** (Metricool gratuit
>   épuisé jusqu'au 01/12 ; il sert seulement à lire les stats). Zernio :
>   gratuit pour 2 comptes, posts illimités (vérifié le 07/11 : `GET
>   /v1/usage`, 0 €), plafond 15 vidéos TikTok / 24 h.
>   - TikTok accountId `6aef19cf4f6bb8199749fd84` (@4_youchoose_4),
>     Instagram accountId `6aef1b2aa9325e24b65c8924` (@4_youchoose_4).
>   - `POST https://zernio.com/api/v1/posts`, en-tête `Authorization: Bearer
>     $ZERNIO_API_KEY`, corps testé OK le 07/11 :
>     `{"content": <caption>, "mediaItems": [{"type":"video","url":
>     "https://raw.githubusercontent.com/diego029929/vid-os-/media/<f>.mp4"}],
>     "platforms": [{"platform":"tiktok","accountId":...},
>     {"platform":"instagram","accountId":...}], "tiktokSettings":
>     {"privacy_level":"PUBLIC_TO_EVERYONE","allow_comment":true,
>     "allow_duet":true,"allow_stitch":true,"content_preview_confirmed":true,
>     "express_consent_given":true,"video_made_with_ai":true,
>     "video_cover_timestamp_ms":600}, "scheduledFor":"AAAA-MM-JJTHH:MM:SS",
>     "timezone":"Europe/Paris"}` (ou `"publishNow": true`).
>   - Changer l'heure : `PUT /v1/posts/{id}` avec `scheduledFor` + `timezone`.
>   - Vérifier : `GET /v1/posts/{id}` (status `scheduled`, puis `published`
>     avec `platformPostUrl`). Noter `zernio_id` dans series/state.json.
>   - Pas de premier commentaire automatique avec Zernio : mettre la question
>     de débat dans la légende.
>   - Au début de chaque routine : `GET /v1/accounts` ; si `needsReconnection`
>     est vrai ou un post de la veille est `failed`, le dire en premier à Fio.
> - **08/11** : les épisodes à publier sont d'abord ceux déjà prêts : partie 2
>   (`ep23.json`, `ep23.mp4` sur media) à 10:00 et SURVIS ? N°8 a déjà été
>   publiée le 07/11 à 20h ; donc 08/11 = partie 2 (10h, déjà rendue),
>   N°9 (12h), partie 3 (17h), N°10 (20h). Ne rendre que les 3 nouvelles.
> - Tout ce qui suit sur « 3 épisodes », « 10h/12h/18h », « 15h/20h30 »,
>   « Metricool » (programmation) est remplacé par ces règles.

Ce fichier est le mode d'emploi de la routine Claude qui tourne chaque matin.
Objectif : créer 3 épisodes d'environ 1 min 30 et les programmer dans Metricool à
**10:00, 12:00 et 18:00 (Europe/Paris)** le jour même, sans intervention humaine.

> **En plus, depuis le 03/11 (test validé par Fio)** : 2 vidéos courtes
> indépendantes « SURVIS ? N°X » de 30-40 s, programmées à **15:00 et
> 20:30**. Tout est décrit dans `series/survis.md` (à lire). Elles passent
> par les mêmes étapes que les épisodes (rendu, contrôle images + Whisper,
> branche media, Metricool TikTok + Instagram), mais APRÈS les 3 épisodes.
> Les noter dans `series/insights.md` avec la mention « courte ».

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

0. Préparer la voix off, en installant d'abord torch en version CPU (sinon
   pip télécharge la version GPU de plusieurs Go et bloque plus de 30 min) :
   `pip install -q torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu`
   puis `pip install -q chatterbox-tts` (≈ 2 min au total).
   **Voix choisie par Fio le 05/11 (« voix 3-A ») : Chatterbox** avec la
   référence `assets/ref/ref-narrateur.wav` (vraie voix de narrateur, livre
   audio LibriVox « Le Père Goriot », domaine public), exagération 0.75,
   cfg 0.3 (moins posée), vitesse 1.2, effet « leger », sans écho. Tout est
   dans `engine/voice_config.json` : ne pas changer sans Fio. Parler-TTS
   (« voix 2 ») a été rejeté par Fio : `./engine/setup_parler.sh` n'est plus
   nécessaire. Fio ne veut PAS la voix d'un autre créateur, ni de service payant.
   Pour faire écouter des voix à Fio : extraits de 3 mots, pas de longues vidéos.
   Les modèles se téléchargent depuis huggingface.co au premier rendu.
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
   - **Accroche** (retour de Fio, 02/11) : PAS de phrase de contexte qui
     revient au début de chaque épisode (interdit en ouverture : « IMAGINE »,
     « IL EST X H », « LE MONDE A FINI... », « TU VAS DEVOIR CHOISIR... »).
     Chaque épisode ouvre différemment, au cœur de l'action : une image
     choc, une réplique de dialogue, un danger immédiat, un détail
     inquiétant. Avant d'écrire, relire les 3 premières répliques des
     épisodes précédents de la série et ne reprendre ni leur forme ni leurs
     mots. Le contexte vient ensuite, glissé dans l'action ;
   - le script **s'enchaîne** : chaque réplique découle de la précédente
     (cause → conséquence), pas une liste de phrases posées ;
   - **jamais « fin de la série » ni « fin de la saison »** à l'écran ou à
     la voix (Fio : ça sert à rien). Le dernier épisode d'une série finit
     comme les autres (dilemme A/B + « ABONNE-TOI POUR LA SUITE ») ;
   - **mauvais choix = « TU ES MORT. »** juste avant le `rewind` (dernier
     plan enregistré avant de rembobiner : `"text": "TU ES *MORT*."`,
     fond rouge, bruitage `hit`). Le moteur l'ajoute tout seul s'il manque ;
   - **chaque épisode se comprend seul** (demande de Fio, 01/11) : un
     spectateur qui tombe dessus sans avoir vu les autres doit tout capter.
     MAIS **jamais de résumé** (« précédemment... », « dans l'épisode
     d'avant... » : Fio trouve ça nul). À la place, écrire mieux :
     - la situation se comprend dès les premières secondes grâce à
       l'action elle-même (ce qu'on voit, ce qui arrive), pas grâce à une
       phrase de contexte toute faite ;
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
     - **TEST DU SPECTATEUR EXTÉRIEUR, OBLIGATOIRE (Fio, 08/11 : « l'enchaînement
       c'est incompréhensible, voir d'un point de vue extérieur si c'est simple
       et captivant »)** : écrire les répliques lues, une par ligne, dans un
       fichier texte, puis lancer un agent neuf (outil Agent, sans autre
       contexte) qui joue un spectateur TikTok de 16-25 ans n'ayant rien vu
       avant. Il lit SEULEMENT ce fichier et donne : résumé en 3 phrases,
       lignes où il est perdu (saut logique, chose pas présentée, contradiction
       avec la règle), si les deux choix se défendent, clarté /10, envie de la
       suite /10. Corriger et refaire le test tant que la clarté est < 8 ou
       qu'il reste une contradiction. Noter les notes dans series/insights.md.
       Erreurs trouvées le 08/11 à ne plus faire : une règle qui se contredit
       (« ne bouge pas » alors qu'il faut continuer de courir), un personnage
       ou un fait qui arrive sans être présenté, une phrase recopiée d'une
       autre vidéo, un choix dont la règle donne la réponse sans aucun prix à
       payer, des phrases vides (« la fin va te glacer ») ;
     - **ÊTRE LE PLUS PRÉCIS POSSIBLE (Fio, 08/11 : « faut être un max précis
       pour que ce soit vraiment simple à comprendre, rapidement »)** :
       chaque réplique se comprend en 2 secondes, à la première écoute.
       Une seule idée par réplique. Toujours dire QUI parle (« Léa : », « les
       haut-parleurs : ») et QUI agit, jamais un « il », « elle », « ça »,
       « ils » ou « la chose » dont on ne sait pas ce que c'est. Des mots
       concrets (« la porte de l'église », pas « là-bas »). Dire POURQUOI le
       héros fait chaque action, et pourquoi le mauvais choix tue. La règle
       du jeu est dite en entier, avec les mêmes mots, dans chaque vidéo.
       Pas de métaphore ni de phrase floue. Le spectateur extérieur doit
       pouvoir répondre sans hésiter : où on est, qui est qui, quelle est la
       règle, ce qui est en jeu au choix ;
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
   (le moteur doit afficher `voix off : chatterbox`) dans un dossier temporaire. Un rendu prend 20 à 35 min : le lancer en arrière-plan et attendre la fin.
   **Un seul rendu à la fois** (02/11 : deux rendus en parallèle dépassent la
   mémoire, le second est tué sans message). Commencer par l'épisode de 10 h ;
   chaque vidéo n'a besoin d'être prête qu'avant son propre horaire. Pour chacune, vérifier
   avec ffprobe la durée (85–95 s) et faire une planche contact
   (`ffmpeg -vf "fps=1/2.5,scale=216:-1,tile=6x4"`) puis la **regarder** :
   texte lisible, rien de coupé, le texte ne cache pas le visage du personnage, pas de mot avec un astérisque visible.
   Le moteur fait déjà écouter chaque réplique par Whisper (via `transformers`,
   modèle openai/whisper-small) et refait celles qui sont mal comprises ou
   bégayées ; il liste à la fin les « RÉPLIQUES ENCORE MAL LUES » : les
   réécrire plus simplement (mots courants, phrase plus courte) et relancer.
   **Écouter aussi la vidéo finale** : si Whisper est disponible (`pip install -q openai-whisper`,
   modèle small, langue fr), transcrire chaque vidéo et comparer au texte :
   un mot répété, bégayé ou incompréhensible = relancer le rendu de cet
   épisode (le moteur retire déjà les répliques au débit anormal, mais pas
   toutes). Écrire les nombres pour qu'ils se lisent bien (le moteur les
   convertit en lettres).
   Corriger et relancer si besoin.
5. Publier les fichiers sur la branche `media` (sans jamais forcer le push) :
   (03/11 : si un rendu tourne encore, NE PAS faire `git checkout media` dans le
   dépôt — `assets/` disparaît et le rendu suivant plante. Utiliser plutôt
   `git worktree add /tmp/media media` et y copier les vidéos une par une.)
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

## Conseils retenus le 02/11 (fiche partagée par Fio)

S'appliquent aux épisodes ET aux courtes « SURVIS ? » :
- **Ancrer en France** : lieux réels et reconnaissables (Paris, Lyon,
  Marseille, une ligne de RER, un TGV Paris-Marseille…), cités dès
  l'accroche. Le spectateur se projette et identifie ses amis.
- **Accroche 0-1 s** : l'image la plus forte de la vidéo d'abord + un texte
  court qui donne lieu et urgence (ex. « LYON, 3 H 12. IL RESTE 9 MINUTES. »),
  sans jamais reprendre la même formule. 1-3 s : une phrase qui promet ce
  qu'on va découvrir.
- **Escalade** : chaque plan plus intense que le précédent, un plan toutes
  les 2-3 s.
- **Faire participer** : la question finale peut proposer de choisir la
  suite (« QUELLE VILLE ENSUITE ? », « QUEL DANGER POUR LE N° SUIVANT ? »).
  Si un commentaire propose une ville ou une idée, la routine peut s'en
  servir et le dire (« VOUS AVEZ CHOISI MARSEILLE »).
- **Hashtags** : 3 à 5 ciblés, dont le nom de la ville (#fiction #survie
  #horreur #marseille…), pas de longue liste.
- **Pas de mention « FICTION »** à l'écran (choix de Fio le 02/11). Ne
  jamais imiter un vrai journal télé, un logo de média ou une alerte
  officielle, et ne rien faire sur une catastrophe réelle en cours.

## Inspiration (demande de Fio, 03/11)

S'inspirer d'histoires connues, de légendes urbaines et de films (horreur,
survie, thriller : jeux d'enfants qui tournent mal comme « Jacques a dit »,
appels d'un numéro inconnu, règles à suivre la nuit, maison hantée, boucle
temporelle, invasion…) pour les ambiances, les thèmes et les ressorts. Les
histoires restent ORIGINALES : ne jamais reprendre l'intrigue, les
personnages, les noms ni les dialogues d'un film ou d'un créateur.
Un spectateur doit reconnaître le genre en 1 seconde (« ah, comme dans tel
film ») puis être surpris par la suite.

## Décors variés (demande de Fio, 04/11 : « c'est toujours les mêmes »)

> **07/11, Fio : « améliorer les décors », « il en faut beaucoup plus,
> limite que tu en crées en fonction du script ». Fio garde le style DESSINÉ
> (il a refusé les décors IA ; le décor `ia` existe dans le moteur mais ne
> doit PAS être utilisé).** RÈGLES :
> - Tous les décors dessinés passent maintenant par `polish()` (matière,
>   rayons de lumière, étalonnage, vignette, grain) : rien à faire.
> - **48 décors** existent (liste : `SCENES` dans engine/render2.py), dont
>   27 ajoutés le 07/11 : salledebain, grenier, cave, cimetiere, eglise,
>   voiture, salon, hopital, classe (`text` au tableau), metro (`text`,
>   `headlights`), plage, phare, grange, tente (`shadow`), bureau, piscine
>   (`floating`), supermarche, laverie (`spin`), bibliotheque, usine, pont,
>   champ (`scarecrow`), tunnel, cabane (`face` à la fenêtre), foraine, toit,
>   aire. Presque tous acceptent `figure` (silhouette aux yeux rouges,
>   `fig_at` [u, v], `fig_size`), `dark`, `red` / `green`.
> - **CHAQUE SÉRIE S'INSPIRE D'UN FILM CONNU (Fio, rappel du 07/11 : « ça
>   peut mieux marcher »)**. Avant une nouvelle série, choisir 1 ou 2 films
>   d'horreur / thriller PEU CONNUS, de niche (Fio, 07/11 : « Squid Game
>   c'est pas assez niche, tout le monde connaît »). PAS de blockbusters
>   (Squid Game, Saw, Ça, Scream, Shining, Destination finale…). Exemples :
>   Pontypool, Coherence, Triangle, Kairo (Pulse), Noroi, Lake Mungo, The
>   Wailing, Session 9, Absentia, The Endless, Ils (2006), Calvaire, La
>   Nuée, Dark Water (2002), The Ritual, A Tale of Two Sisters, The Void,
>   Resolution, Lovely Molly, The Blackcoat's Daughter (jamais de gore).
>   Ne pas réutiliser un film déjà pris par une série précédente. Noter en
>   tête du fichier de la série : film(s) source, ce qu'on reprend (le
>   principe, l'ambiance, le type de lieux, le type de danger) et ce qui
>   change (lieu en France, personnages, règles). Les DÉCORS de la série
>   reprennent l'ambiance des lieux du film (ex. Shining → hôtel isolé,
>   long couloir à moquette, chambre 237 → chez nous un autre numéro).
>   Histoire, noms et dialogues 100 % originaux.
> - **CHAQUE PLAN MONTRE CE QUE DIT SA PHRASE (Fio, 07/11, vidéo de
>   référence : « tu vois les décors suivent le script »)**. Pour chaque
>   plan, se demander : « qu'est-ce que la phrase montre ? » et mettre CETTE
>   image. « Un message » → le téléphone avec le message à l'écran ; « la
>   télé s'allume » → la télé ; « ta grand-mère » → sa maison ; « 3 h » →
>   l'horloge ou l'écran verrouillé à 3:00 ; « la porte » → la porte. Le
>   héros vu de dos devant le lieu sert de liaison entre ces plans.
>   Plans « objet » en gros plan disponibles : `telephone` (`mode` "lock"
>   avec `time`, `date`, `notif` [titre, texte] ; "chat" avec `contact` et
>   `messages` [["lui"|"moi", texte], …] ; "call" avec `contact` ; `crack`
>   écran fêlé ; `sleeve` couleur de la manche) et `tele` (`face` visage
>   dans la neige, `text` mot rouge à l'écran, `off`). Si la phrase parle
>   d'un objet qui n'a pas encore de plan (lettre, radio, photo, clé,
>   miroir, poupée…), DESSINER un plan objet `scene_<objet>` sur le modèle
>   de `scene_tele` (objet en grand au centre, pièce floue derrière avec
>   `_room_blur`). Au moins 4 plans « objet » par épisode. On s'inspire de
>   l'idée, on ne recopie pas le visuel d'un autre créateur.
> - Ambiance (07/11, idem) : `polish()` rend maintenant tout plus sombre et
>   plus doux (couleurs moins vives, hautes lumières adoucies).
> - **CHAQUE SÉRIE A SES PROPRES DÉCORS (Fio, 07/11 : « construire les
>   décors en fonction de la série »)** : quand une nouvelle série commence,
>   AVANT d'écrire l'épisode 1, dessiner 5 à 7 décors propres à son univers
>   (lieux typiques de la ville / région, bâtiment central de l'histoire,
>   maison du héros, le « méchant » dans son décor), nommés `<sigle>_<lieu>`
>   (ex. `jad_place` pour « Jacques a dit »), avec une option `aube` ou
>   équivalent pour le dernier épisode. Les lister dans le fichier de la
>   série (section Décors) et les utiliser au moins 3 fois par épisode.
>   Modèle : les décors `jad_*` (helpers `_granite_house`, `_horn`,
>   `_jacques`).
> - **CRÉER DES DÉCORS EN FONCTION DU SCRIPT, À CHAQUE VIDÉO** : après avoir
>   écrit le script, lister les lieux. Pour chaque lieu qui n'existe pas
>   (ou qui ne colle pas vraiment), DESSINER un nouveau décor : fonction
>   `scene_<lieu>(p)` dans engine/render2.py (juste avant `def scene_old`),
>   ajoutée à `SCENES`, sur le modèle des décors existants (Canvas, `c.glow`,
>   `c.soft`, `_moon`, `_stars`, `_fig`, `_end`). Au moins **2 nouveaux
>   décors par vidéo**, détaillés (au moins 8 éléments : murs/sol, objets,
>   une ou deux sources de lumière avec `c.glow`, un détail qui fait peur),
>   couleurs de nuit violet / orange, pas de blanc pur en grande surface.
>   Vérifier chaque nouveau décor sur une planche contact AVANT le rendu
>   (rien de cramé, rien de vide, le lieu se reconnaît) et le corriger.
> - **`flou` = au plus 1 plan sur 3.** **Épisode : au moins 7 décors
>   différents ; courte : au moins 5.** Changer de décor tous les 3-4 plans.
>   Ne pas reprendre le décor principal de la vidéo précédente.
> - Commiter les nouveaux décors sur main avec les épisodes : la
>   bibliothèque grandit chaque jour.

## Bonne réponse A ou B au hasard (demande de Fio, 04/11 : « c'est toujours B »)

Jusqu'ici la mauvaise option était toujours A (jouée en premier) et la bonne
toujours B : les spectateurs l'ont remarqué. Pour CHAQUE vidéo, tirer au sort
AVANT d'écrire le script :
`python3 -c "import random; print(random.choice('AB'))"`
et noter le résultat dans `series/insights.md`. La lettre tirée est la
**bonne** réponse : mettre l'option gagnante sur cette carte (`a` ou `b`).
La mauvaise option est toujours jouée en premier (`record`, « TU ES MORT. »,
`rewind`), puis la bonne : adapter les `picked` en conséquence (si la bonne
est A : premier `picked` = "B", second = "A"). Sur 5 vidéos d'un même jour,
au moins une bonne réponse A et au moins une B ; si le tirage donne 5 fois
la même lettre, inverser la dernière.

## Faire venir abonnés et commentaires (demande de Fio, 04/11 : « fais-les venir »)

Objectif : 10 000 abonnés (monétisation TikTok). Vues ~800, commentaires
presque nuls → chaque vidéo DOIT contenir ces leviers (concept inchangé) :

1. **Commenter AVANT la réponse** : pendant le compte à rebours du choix,
   le texte dit « ÉCRIS A OU B EN COMMENTAIRE, VITE » (05/11 : la voix Parler lit
   mal « A OU B » : écrire plutôt « ÉCRIS TON CHOIX EN COMMENTAIRE, VITE »
   et « TON CHOIX ? LA RÉPONSE DANS LA PARTIE X+1 », les cartes A/B restent) (le spectateur
   commente avant de voir la réponse ; c'est le commentaire le plus facile).
2. ~~Teaser de rétention~~ SUPPRIMÉ le 08/11 : ces phrases (« presque tout
   le monde se fait avoir », « la fin va te glacer ») ne racontent rien et
   cassent l'enchaînement. La tension vient de l'histoire elle-même.
3. **« PARTIE X »** en gros dès la première seconde (`subtitle`) et dans le
   titre ; couverture de la vidéo = image de l'accroche avec « PARTIE X » :
   passer `videoCoverMilliseconds` (≈ 600) dans `createScheduledPost`.
4. **Fin = dilemme qui divise** : deux options défendables, aucune évidente,
   puis « A OU B ? LA RÉPONSE DANS LA PARTIE X+1 » et « ABONNE-TOI POUR NE
   PAS LA RATER ». La partie suivante commence en donnant la réponse
   (« VOUS ÉTIEZ 60 % À DIRE A… ») sans résumé de l'épisode.
5. **Premier commentaire** : `firstCommentText` dans `createScheduledPost`
   = une question qui lance le débat (« Moi j'aurais choisi B. Et toi ? »,
   « Qui aurait survécu ici ? 👇 »), différente à chaque vidéo.
6. **Légende** : la première ligne est une question directe au spectateur
   (« Tu décroches ou tu laisses sonner ? »), puis 3 à 5 hashtags.
7. **Lire les commentaires** dans les stats chaque matin : si quelqu'un
   propose une idée, une ville ou un choix, s'en servir et le dire dans la
   vidéo (« VOUS M'AVEZ DIT : LE GRENIER »). Ça pousse les autres à
   commenter.
8. Dans `series/insights.md`, suivre chaque jour commentaires et abonnés
   gagnés par vidéo, et garder les formulations qui en font le plus.

## Donner une vraie raison de s'abonner (Fio, 04/11 : « abonne-toi » ne fait pas follow)

Choix de Fio le 04/11 : **seulement la coupure avant la réponse** (pas de
compteur de vies, pas d'heure de rendez-vous annoncée ; ne pas mettre
`lives` dans les JSON).

- La vidéo s'arrête pile sur le dilemme final, cartes A/B affichées, sans
  révélation. Dernier plan : « LA RÉPONSE DANS LA PARTIE X+1 ». On peut
  finir par « ABONNE-TOI POUR NE PAS LA RATER », jamais un « abonne-toi »
  seul.
- La partie suivante commence par cette réponse (sans résumé de l'épisode).
- Pour les courtes « SURVIS ? » : même principe, « LA RÉPONSE DANS LE
  N° SUIVANT ».
