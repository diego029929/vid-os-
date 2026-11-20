# Routine quotidienne (depuis le 15/11 : séries d'horreur COURTES ; dès le 16/11 : style « Nuit & téléphone »)

> **NOUVEAU 15/11 au soir (choix de Fio) : toutes les vidéos se font dans le
> style « Nuit & téléphone »** avec `engine/nuit.py` (voir § 1 bis), y compris
> les parties 2 et 3 des 4 séries en cours (mêmes histoires, nouveau dessin).
> `engine/render2.py` (style 2) n'est plus utilisé pour publier.

Ce fichier contient SEULEMENT les règles en vigueur. Il prime sur le message
de la tâche planifiée (qui parle encore de 5 vidéos et de Metricool : il ne
peut pas être modifié). L'historique est dans `series/insights.md`.

## 0. Pourquoi ce format (demande de Fio, 14/11 soir)

Fio a trouvé « nul » le concept du 14/11 (Bataille de pays + Tu préfères :
ARRÊTÉ, ne plus en faire) et a demandé : « refais les vidéos qu'on faisait
avant avec de meilleures animations », puis « juste fais des séries plus
courtes ». On revient donc aux séries d'horreur dessinées (style 2), mais :
- **épisodes de 35 à 45 s** (au lieu de 90 s) : c'était le défaut des
  anciennes séries (les gens partaient au bout de 6-14 s) ;
- **séries de 3 épisodes** (au lieu de 4-6) ;
- **animation 2** (engine/anim.py + render2.py, 14/11) : bouche qui bouge
  quand un personnage parle, personnages qui entrent dans le cadre,
  transitions glissées, coup de zoom sur le mot en rouge, caméra plus ample,
  silhouette qui traverse le fond (`passant`), éclairs (`eclair`).
Formats ARRÊTÉS : défis, quiz, 4 indices, intrus, fruits, bataille de pays,
tu préfères, SURVIS. Permission de Fio (10/11) : Claude peut changer de
format sans demander quand les stats le justifient, mais Fio vient de
choisir celui-ci : le garder tant que Fio ne dit pas le contraire.

## 1. Le format

- **4 séries en parallèle, 1 épisode de chacune par jour**, TikTok +
  Instagram (Reel) :
  | Heure (Paris) | 10:00 | 12:00 | 18:00 | 20:00 |
  |---|---|---|---|---|
  | Vidéo | série n°1 | série n°2 | série n°3 | série n°4 |
- **Séries de 3 épisodes.** Les 4 séries commencent le même jour et finissent
  ensemble 3 jours plus tard ; le lendemain, 4 NOUVELLES séries. 1er cycle :
  15/11, 16/11, 17/11. Séries en cours : `series/state.json` →
  `parallel_series` (pour chaque horaire : `slot`, `series`, `series_file`,
  `episode_count` = 3, `next_episode`, `prefix`).
- **Le 15/11 à 10:00 : « La Station », partie 1 est DÉJÀ PRÊTE**
  (`episodes/station-01.json`, essai montré à Fio le 14/11, série
  `series/la-station.md`) : la rendre telle quelle (sauf si Fio a demandé un
  changement) ; écrire seulement les 3 autres séries.
- **Épisode de 35 à 45 s, ≤ 800 caractères lus, 9 à 12 plans** (format
  du JSON : § 1 bis). Forme :
  1. Accroche = 1re phrase, la situation en moins de 10 mots, au cœur de
     l'action (un message, un bruit, une règle). Jamais de titre lu.
     Idéal : le 1er plan est un écran de téléphone (notif, appel, SMS).
  2. Histoire en ligne droite : 1 lieu principal, 1-2 personnages, 1-2
     règles (plan `"regle"` juste après le moment où la règle compte).
  3. Montrer ce que dit la phrase : un message → plan `tel` ; on toque →
     `objet` porte ; quelqu'un derrière → `ombre` ; peur → `"hero":
     "peur"`, `"cadre": "gros"`.
  4. Fin : plan `"choix"` (1 · … OU 2 · …), voix « … ? Écris #un# ou
     #deux#. ». Pas de « abonne-toi ». Les deux choix se défendent et ont
     un prix. Choix UNIQUEMENT à la fin, jamais au milieu.
  5. Le vote décide vraiment : la partie suivante commence par le choix qui
     a gagné. Moins de 3 votes = tirage au sort. Noter dans
     `series/state.json` → `votes`.
  6. Partie 3 (dernière) : jamais « fin de la série » ; elle finit aussi
     sur un vote (« la suite si vous êtes nombreux à voter »).

## 1 bis. Style « Nuit & téléphone » (engine/nuit.py, choisi par Fio le 15/11)

Fio a vu les exemples publics de Scénar.app (pack de prompts payant, NON
acheté) et veut ce rendu. On le refait nous-mêmes, gratuit : dessin plat 2D
de nuit, perso à capuche turquoise aux yeux mi-clos, écrans de téléphone
redessinés (appel, SMS, notification, localiser, photo), horloge qui tourne
en haut (« ● PARTIE 2 · COULOIR / 03:00:12 »), carte rouge « RÈGLE N°1 »,
sous-titres Anton 1-2 mots (mots clés rouges ou jaunes), choix final
orange/bleu « 1 · … OU 2 · … ». Exemple complet : `episodes/exemple-nuit.json`
(rendu : /mnt/project-files/essais-scenar/exemple-episode-complet.mp4).

**Une commande fait tout** (voix Chatterbox de la routine, calage des
sous-titres par Whisper small, bruitages, dessin filmé par Playwright) :
`python3 engine/nuit.py episodes/<f>.json /tmp/<f>.mp4` (≈ 6 min pour 40 s,
surtout la voix). D'abord un brouillon sans voix pour vérifier le dessin :
`python3 engine/nuit.py episodes/<f>.json /tmp/b.mp4 --brouillon` (≈ 1 min)
puis planche contact.

**Format du JSON** (`"style": "nuit"`) :
- en tête : `series`, `etiquette` (« PARTIE 2 »), `heure` de départ de
  l'horloge (« 02:59:48 »), `title`, `caption`, `vote` (petite ligne sous le
  choix : « Le plus de votes décide la partie 3 »), `hero` (`couleur`, `voix`
  si le héros parle), `persos` : `{"LÉA": {"couleur": "#e0607e",
  "cheveux": true, "voix": "ref-femme-1.wav"}}` (voix dans `assets/ref/`).
- `beats` = 9 à 12 plans, **un plan par phrase lue** (`voice`). Mots en
  couleur dans `voice` : `*mot*` rouge (danger, 1 par plan au plus),
  `#mot#` jaune (heure, chiffre, « un » / « deux » du vote). Chaque plan est
  UN de ces types :
  - **décor** : `"vue"` = `rue` (le décor défile si le héros marche),
    `chambre`, `couloir`, `salon`, `cuisine`, `escalier`, `foret`,
    `station`, `mer`, `hopital`, `cave`, `voiture`, `sdb` ; `"hero"` =
    `marche` / `debout` / `sonne` (téléphone qui vibre, zoom) / `peur`
    (grands yeux, tremble) / `dos` / `absent` ; `"hx"` position 0-1 ;
    `"cadre"` = `large` / `gros` (gros plan visage) / `pousse` ;
    `"persos": [{"nom": "LÉA", "x": 0.3, "etat": "peur"}]` ;
    `"qui": "LÉA"` = c'est elle qui parle (sa voix, sa bouche bouge ;
    `"MOI"` pour le héros) ; `"ombre": true` ou `{"x": 0.25}` = silhouette
    noire aux yeux blancs qui apparaît ; `"flicker": true` = lumière qui
    clignote ; `"pluie"` / `"neige"` / `"eclair"` / `"rouge_lum"` : true ;
    `"reflet": true` (miroir de `sdb`) ; `"lieu"` = texte de l'horloge si
    besoin (sinon le nom du décor).
  - **téléphone** : `"tel": {"type": "appel", "nom": "Moi", "num": "…"}`,
    `{"type": "sms", "de": "Inconnu", "inconnu": true, "lignes": ["…", "…"],
    "moi": [1]}` (indices des bulles envoyées par le héros), `{"type":
    "notif", "app": "LOCALISER", "titre": "…", "texte": "…", "heure":
    "3:04"}`, `{"type": "localiser", "titre": "AirTag inconnu"}`,
    `{"type": "photo", "vue": "chambre", "ombre": true}`. Le décor du plan
    d'avant reste derrière, assombri.
  - **objet plein écran** : `"objet": {"type": "porte", "toc": true}` (ou
    `"ouverte": true`), `lettre` (`texte`), `cassette` (`texte`), `horloge`
    (`heure`), `photo` (`vue`, `ombre`, `texte`).
  - **règle** : `"regle": {"n": 1, "txt": "Après minuit,\nn'ouvre à
    personne"}` (bruit sourd automatique). La voix lit la règle.
  - **choix** (DERNIER plan, obligatoire) : `"choix": {"a": "Ouvrir la
    porte", "b": "Appeler la police"}`, voix : « Tu ouvres, ou tu appelles
    la police ? Écris #un# ou #deux#. » Les votes se comptent en « 1 » / « 2 »
    (« A » / « B » aussi acceptés).
  - bruitages automatiques : SMS = « ding », appel = sonnerie, `sonne` =
    vibreur, règle = boum ; sinon `"sfx": "toc" | "souffle" | "boom" |
    "vibre" | "sonnerie" | "message"` (ou `["toc", 0.4]` = décalé de 0,4 s).
- Rythme du style : au moins 3 plans téléphone/objet par épisode (c'est ce
  qui fait le style), le reste en décors ; jamais 2 plans de suite
  identiques ; `ombre` ou `flicker` dès que le danger arrive.
- Décor qui manque pour une série : l'ajouter dans `DECORS` de
  `engine/nuit.js` (même style : aplats violets, fenêtres jaunes, `lamp()`,
  `win()`, `door()`, `floor()`), puis brouillon + planche avant le rendu.

## 1 ter. Edits GTA 6 (EN PLUS des 4 séries ; format changé par Fio le 19/11)

> Fio, 19/11 : « J'voulais une édit avec de vraies images GTA, pas ça » et
> « pas obligé de mettre de voix, juste un son d'edit ». Le format dessiné
> + voix (gta6-01/02, publiés le 19/11) est ARRÊTÉ.

- **2 edits par jour, 08:00 et 09:00 (Paris)**, TikTok + Instagram, en plus
  des 4 épisodes (6 vidéos/jour). Ne pas toucher aux créneaux 10h/12h/18h/20h.
- **20/11 : DÉJÀ programmé** : seulement 9h (gta6-edit-02, « Lucia edit »).
  L'edit de 8h (bande-annonce) a été ANNULÉ par Fio (« juste le son est
  nul… garde celle de 9h, pas celle de 8h »). Ne rien refaire le 20/11 ;
  commencer le 21/11 avec gta6-edit-03 (8h) et 04 (9h).
- **Edit = ≈ 17 s, AUCUNE voix**, vraies images officielles coupées sur le
  beat, zooms, flashs, 1-2 textes courts (Anton), fin sur le logo + une
  question à commenter (« 1 ou 2 »). Commande :
  `python3 engine/edit.py episodes/gta6-edit-NN.json /tmp/gta6-edit-NN.mp4`
  (≈ 2 min). Modèles : `episodes/gta6-edit-02.json` (captures `"image"`,
  le modèle que Fio a GARDÉ) et `gta6-edit-01.json` (extraits de la
  bande-annonce, `"t"` = seconde de la source). Format du JSON en tête de
  `engine/edit.py`. Privilégier les edits par personnage / lieu à partir
  des captures.
- **Son = un VRAI morceau, jamais le beat maison** (`engine/beat.py`, jugé
  nul par Fio le 19/11). Seulement des morceaux Creative Commons **CC BY ou
  CC BY-SA** (PAS « NC », PAS « ND », jamais de musique connue). Les
  trouver avec l'API Openverse (gratuite, sans clé) :
  `curl -s -G https://api.openverse.org/v1/audio/ --data-urlencode q=trap
  --data-urlencode license=by,by-sa --data-urlencode source=jamendo`,
  puis télécharger l'URL `prod-1.storage.jamendo.com/?trackid=…&format=mp32`
  dans `/tmp/gta6/son.mp3` (Wikimedia, Freesound et ccMixter refusent le
  conteneur : ne pas insister). Dans le JSON : `"musique": {"fichier":
  "/tmp/gta6/son.mp3", "chercher": [a, b], "credit": "…"}` : `edit.py`
  trouve le tempo et le « drop » (librosa) et le place au temps 8 (y
  mettre `"flash": true`). Morceaux validés : « Miami Trap (Club Mix) » de
  Hasenchat (trackid 1301348, `"chercher": [30, 50]`) et « 09 Trap Bells
  (Instrumental Mix) » de Hasenchat (trackid 1253537, `"chercher": [18,
  40]`), CC BY-SA 3.0. Éviter > 150 BPM (vidéo < 15 s). **Toujours
  créditer** en fin de légende : « 🎵 Titre – Artiste (CC BY-SA 3.0) ».
- **Images : seulement les fichiers OFFICIELS que Rockstar met en
  téléchargement** sur rockstargames.com/VI/downloads (pas YouTube) :
  ```
  mkdir -p /tmp/gta6 && cd /tmp/gta6
  B=https://media-rockstargames-com.akamaized.net/VI/downloads
  curl -sL -o launch.mp4 $B/videos/GTAVI_Launch_Trailer/GTAVI_Launch_Trailer.mp4   # 780 Mo, 4K, 89 s
  curl -sL -o shots.zip $B/screenshots/GTAVI_Screenshots.zip && unzip -q shots.zip -d shots   # 138 captures 4K
  ```
  (aussi : `GTAVI_Vintage_Vice_City_Pack.zip`, `GTAVI_Ultimate_Edition_Benefits.zip`,
  `artwork_wallpapers/GTAVI_Artwork_Wallpapers.zip` ; relire la page
  `rockstargames.com/VI/downloads` : de nouvelles vidéos peuvent arriver).
  Ne pas télécharger `GTAVI_An_Extended_Look.mp4` (14 Go). La bande-annonce
  a des bandes noires : garder `"bandes": 0.0556`.
- **Un thème par edit, jamais 2 fois le même** (noter dans
  `series/state.json` → `gta6.deja_traite`) : Lucia, Jason, Vice City de
  nuit, les voitures, la plage, les Keys, les braquages, les persos
  secondaires (dossiers `shots/People/*`), Leonida (`shots/Places/*`),
  « avant / après » GTA 5… Alterner : 8h = extraits de la bande-annonce,
  9h = captures.
- **Cadrage 9:16** : faire une planche des images en 16:9 avec une grille,
  et régler `"x"` pour que le visage/sujet soit dans l'image :
  `x = (centre du sujet − 0,15) / 0,70` (0 = gauche, 1 = droite). Vérifier
  la planche de l'edit (`fps=2,tile=10x4`) : aucun visage coupé, pas de
  bande noire, pas de plan tout blanc.
- Contrôle : `python3 engine/check_video.py /tmp/gta6-edit-NN.mp4 --min 15
  --max 30` (le « silence » n'existe pas ici). Zernio : comme § 5 mais
  `"video_made_with_ai": false`. Légende : une question + « 👇 » +
  `#gta6 #gtavi #gta #edit` + 1 tag.
- Risque connu : ce sont des images de Rockstar (mises en téléchargement
  par Rockstar pour les fans et la presse). Si TikTok/Instagram retire une
  vidéo ou met un avertissement, ARRÊTER les edits et le dire à Fio.

## 2. Règles d'écriture (Fio)

- **Clair et précis** : chaque réplique se comprend en 2 secondes. Une idée
  par réplique. Dire qui parle et qui agit, jamais un « il », « ça » ou « la
  chose » flou. Dire pourquoi le héros agit.
- Script fluide : chaque phrase découle de la précédente. Jamais de phrase
  coupée sur deux plans. Pas de phrase vide.
- **Chaque épisode se comprend seul**, sans résumé. Personnages, règle et
  lieu présentés dans les 3 premières lignes.
- Ancrer en France. Tutoiement, présent, jamais gore.
- **S'inspirer de films de NICHE, jamais les recopier** (pas de
  blockbuster). Exemples : Coherence, Triangle, Kairo, Noroi, Lake Mungo, The
  Wailing, Session 9, Absentia, The Endless, Calvaire, La Nuée, Dark Water
  (2002), A Tale of Two Sisters, The Void, Lovely Molly, Vacancy. Déjà
  pris : Pontypool + Ils (Jacques a dit), The Ritual + Resolution (Le
  Refuge), Vacancy + Kairo (La Station), Dark Water (L'eau du septième), Session 9
  (La Bande), Lake Mungo (La Photo), Coherence (La Coupure), Absentia (Le
  Tunnel), The Void (Chambre neuf), Triangle (Le Ferry). Noter le film en tête du fichier
  de la série. Les 4 séries d'un cycle ont 4 lieux et 4 ambiances
  différents.
- Légende (`caption`) : 1re ligne = la question du vote + « Le plus de votes
  décide la partie X+1 👇 », puis 3 à 5 hashtags. `title` ≤ 80 caractères,
  commence par « Partie N · ».

## 3. Les décors (dessinés, adaptés au script)

> Depuis le style « Nuit & téléphone » : les décors sont ceux de
> `engine/nuit.js` (§ 1 bis). Les règles ci-dessous sur `render2.py` ne
> servent plus ; garder seulement « chaque plan montre ce que dit sa
> phrase » et « au moins 5 vues différentes par épisode ».

- Style DESSINÉ uniquement (le décor `ia` est interdit). 60+ décors dans
  `SCENES` (`engine/render2.py`) : les réutiliser.
- **Chaque nouvelle série : au moins 2 décors propres** `<sigle>_<lieu>`
  dessinés dans `engine/render2.py` (fonction `scene_<lieu>(p)`, ajoutée à
  `SCENES`) avant l'épisode 1, listés dans le fichier de la série.
- **Chaque plan montre ce que dit sa phrase** (« un message » → le
  téléphone, « la porte » → la porte). Au moins 5 décors différents par
  épisode, `flou` sur 1 plan sur 4 au plus.
- Vérifier chaque nouveau décor sur une planche AVANT le rendu : l'horloge
  cache les 15 % du haut (rien d'important au-dessus de v ≈ 0.25), garder
  le texte entre u = 0.2 et 0.8, l'ambiance « rouge » assombrit beaucoup.
- `"meteo": "pluie" | "neige" | "cendres"` sur les plans dehors.

## 4. La voix (choix de Fio, ne pas changer sans Fio)

- **Depuis le 17/11 : la voix de femme des premières vidéos** (Fio, 16/11
  soir : « la voix de femme initiale des premières vidéos », celle de
  « L'ascenseur » fin octobre) = voix Piper gratuite `fr_FR-upmc-medium`,
  locutrice 0, effet « megaphone », tempo 1.1 (`engine/voice_config.json`).
  C'est la voix du NARRATEUR ; les personnages qui ont `"voix"` gardent leur
  voix Chatterbox. `engine/nuit.py` télécharge le modèle Piper tout seul au
  premier rendu (`engine/get_voice.sh`, huggingface.co). Plus de voix
  d'homme (ref-pierre-moyen, ref-narrateur-grave) pour le narrateur. Jamais
  baisser la hauteur artificiellement, jamais de service payant, jamais la
  voix d'un autre créateur.
- ≈ 17,5 caractères lus par seconde avec `--verif` (pauses comprises) → ≤ 830
  caractères lus par épisode (880 car. = 50,5 s, refusé) ; si l'épisode fait
  < 35 s, ajouter une phrase.
- Mots mal lus à éviter : « N° » (dire « numéro »), « sweat » (« pull »),
  ville seule en début de phrase, « village », « grésiller », répliques de 3
  mots ou moins, « défi », « fruit », mots d'une syllabe ou en « -illé » en
  fin de phrase (« pain », « grillé »), « revenir », « ne réponds pas » (lu
  « n'en réponds pas » → « ne réponds jamais »), « Ta mère t'écrit : » (lu
  « t'écriste » → « Message de ta mère : »), « Tu hésites » en tout début
  (→ « Alors, tu hésites »), « moi. Viens seul » (phrases collées), « tire-la »,
  un prénom (« Hugo ») au milieu de la question finale, un « ou » après une
  virgule dans la question finale (→ « ou alors, »). Nombres en lettres ; phrase
  lue différente de l'affichage dans `"voice"`.
- Piper (narrateur depuis le 17/11) n'est PAS identique d'un rendu à l'autre
  (vu le 18/11 : une phrase juste au 1er rendu devient floue au suivant).
  Après chaque rendu, retranscrire toute la vidéo ; si une phrase douteuse,
  la découper (ffmpeg 3-5 s) et la retranscrire seule avant de conclure.
  Une tournure qui échoue 2 fois : la CHANGER. Tester une tournure douteuse seule
  (`voice.synth` + Whisper medium) avant de relancer un rendu.

## 5. Les étapes de chaque matin

0. Installer : `pip install -q torch==2.6.0 torchaudio==2.6.0 --index-url
   https://download.pytorch.org/whl/cpu`, puis `pip install -q
   chatterbox-tts piper-tts language_tool_python openai-whisper playwright` puis
   `pip install -q --no-deps num2words` (pour `--verif`) et `pip install -q librosa` (edits GTA) et `pip install -q librosa` (edits GTA) (≈ 3 min ;
   Playwright utilise le Chromium déjà installé `/opt/pw-browsers/chromium`,
   ne PAS lancer `playwright install`). Si
   l'installation échoue : ne rien publier, le dire.
1. **Zernio** : `GET /v1/accounts`. Si un compte a `needsReconnection` ou si
   un post de la veille est `failed`, le dire à Fio en premier.
2. **Stats et votes** (`GET /v1/analytics` ; commentaires : `GET
   /v1/inbox/comments/{platformPostId}?accountId=…`) : vues, likes,
   commentaires, partages, temps moyen (`igReelsAvgWatchTime`, ms),
   `completionRate`. Compter les votes A/B de la veille. Tout noter dans
   `series/insights.md` (une section par jour).
3. **Écrire les 4 épisodes** (`episodes/<prefix>-NN.json`, `"style": "nuit"`, § 1 bis),
   en commençant par celui de 10:00. Nouvelle série : écrire d'abord
   `series/<slug>.md` (film source, univers, règle, personnages, décors,
   tableau des 3 épisodes) et dessiner ses décors.
4. **Test du spectateur extérieur, obligatoire** : écrire les répliques lues
   (une par ligne) dans un fichier, puis lancer un agent neuf (outil Agent,
   sans autre contexte) qui joue un spectateur TikTok de 16-25 ans n'ayant
   rien vu : résumé en 2 phrases, lignes où il est perdu, si les deux choix
   se défendent, clarté /10, envie de la suite /10. Corriger tant que la
   clarté est < 8.
5. Relecture : `python3 engine/check_script.py episodes/<f>.json`.
6. **Rendu, UN SEUL À LA FOIS**, dans l'ordre des horaires : brouillon
   `python3 engine/nuit.py episodes/<f>.json /tmp/b.mp4 --brouillon` +
   planche, puis `python3 engine/nuit.py episodes/<f>.json /tmp/<f>.mp4`
   (≈ 6 min pour 40 s).
   Vérifier avec `pgrep` qu'aucun autre rendu ne tourne. Ne pas lancer
   Whisper pendant un rendu (4× plus lent).
7. **Contrôles avant publication** :
   - planche contact (`ffmpeg -i v.mp4 -vf "fps=1/1.6,scale=216:-1,tile=6x4"
     -frames:v 1 p.png`) à REGARDER : texte lisible, rien de coupé, chaque
     plan montre sa phrase, la carte de règle ne cache rien d'important ;
   - voix : transcription Whisper (medium, fr) comparée au texte. Mot
     répété, bégayé ou mal dit = changer la phrase et relancer. En cas de
     doute, découper 8-10 s avec ffmpeg et retranscrire ;
   - `python3 engine/check_video.py /tmp/<f>.mp4 --min 30 --max 50` doit
     dire OK.
   Ne jamais publier une vidéo défectueuse.
8. **Branche `media`** (jamais de push forcé, jamais de MP4 sur main) :
   `git worktree add /tmp/media media` (ne PAS faire `git checkout media`),
   supprimer les vidéos déjà publiées, copier les nouvelles, commit, `git
   push origin media`.
9. **Programmer dans Zernio** dès que la vidéo est prête :
   `POST https://zernio.com/api/v1/posts`, `Authorization: Bearer
   $ZERNIO_API_KEY`, corps :
   `{"content": <caption>, "mediaItems": [{"type": "video", "url":
   "https://raw.githubusercontent.com/diego029929/vid-os-/media/<f>.mp4"}],
   "platforms": [{"platform": "tiktok", "accountId":
   "6aef19cf4f6bb8199749fd84"}, {"platform": "instagram", "accountId":
   "6aef1b2aa9325e24b65c8924"}], "tiktokSettings": {"privacy_level":
   "PUBLIC_TO_EVERYONE", "allow_comment": true, "allow_duet": true,
   "allow_stitch": true, "content_preview_confirmed": true,
   "express_consent_given": true, "video_made_with_ai": true,
   "video_cover_timestamp_ms": 600}, "scheduledFor": "AAAA-MM-JJTHH:MM:00.000Z"}`
   (heure UTC = Paris − 1 h en hiver ; avec un champ `timezone`, Zernio
   répond « Invalid date ») (ou `"publishNow": true` si l'heure est
   passée). Vérifier avec `GET /v1/posts/{id}`. Noter `zernio_id` dans
   `series/state.json` → `published`. Zernio est gratuit (2 comptes, 15 vidéos TikTok /
   24 h). Metricool ne sert plus à publier.
10. **Enregistrer sur main** : JSON d'épisodes, fichiers de série,
    `series/state.json` (`parallel_series` : avancer `next_episode` ;
    ajouter les vidéos à `published` avec `zernio_id`), `series/insights.md`
    et les nouveaux décors de `engine/nuit.js`.
11. **Résumé court en français pour Fio** : les 4 titres, les horaires, les
    réseaux, les votes de la veille, ce que les stats disent (vues, temps
    moyen, complétion) et ce qui change.
