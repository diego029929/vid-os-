# Routine quotidienne (depuis le 15/11 : séries d'horreur COURTES, mieux animées)

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
- **Épisode de 35 à 45 s, ≤ 800 caractères lus, 10 à 13 plans.** Forme :
  1. Accroche = 1re phrase, la situation en moins de 10 mots, au cœur de
     l'action (un message, un bruit, une règle). Jamais de titre lu.
  2. Histoire en ligne droite : 1 lieu principal, 1-2 personnages, 1-2
     règles (carte `"rule"` sur le plan où elle est dite OU testée, jamais
     sur un gros plan visage ni sur un plan où l'image montre déjà le
     texte de la règle).
  3. Lumière : `"mood": "bleu"` au départ, `"rouge"` quand le danger
     apparaît, `"noir"` pour la fin.
  4. Fin : vote A/B (2 plans : « A : … B : … » puis « LE PLUS DE VOTES
     DÉCIDE LA PARTIE X+1. ÉCRIS TON CHOIX EN COMMENTAIRE. », avec
     `"no_whip": true`). Pas de « abonne-toi » (trop long). Les deux choix
     se défendent et ont un prix. A/B UNIQUEMENT à la fin, jamais au milieu.
  5. Le vote décide vraiment : la partie suivante commence par le choix qui
     a gagné. Moins de 3 votes = tirage au sort. Noter dans
     `series/state.json` → `votes`.
  6. Partie 3 (dernière) : jamais « fin de la série » ; elle finit aussi
     sur un vote (« la suite si vous êtes nombreux à voter »).
- **Animation à utiliser** (tous les épisodes) :
  - au moins 1 plan `"passant"` par épisode (silhouette qui traverse le
    fond : `true` ou `{"y": pied 0-1, "h": taille, "sens": 1/-1}`), sur un
    plan SANS personnage en gros plan, quand le texte parle de quelqu'un ;
  - `"eclair": true` sur 1 plan dehors avec `"meteo": "pluie"` ;
  - dialogues : quand un personnage parle (« LÉA : … »), mettre
    `"parle": true` dans son `char` (sa bouche bouge avec la voix) ;
  - mot fort en rouge avec `*mot*` (1 par plan au plus) : la caméra fait un
    coup de zoom dessus ;
  - varier `cam` (zoom avant/arrière, panoramique) d'un plan à l'autre.

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
  Refuge), Vacancy + Kairo (La Station). Noter le film en tête du fichier
  de la série. Les 4 séries d'un cycle ont 4 lieux et 4 ambiances
  différents.
- Légende (`caption`) : 1re ligne = la question du vote + « Le plus de votes
  décide la partie X+1 👇 », puis 3 à 5 hashtags. `title` ≤ 80 caractères,
  commence par « Partie N · ».

## 3. Les décors (dessinés, adaptés au script)

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

- Chatterbox + `assets/ref/ref-narrateur-grave.wav` (« voix 1 », choisie le
  09/11). Réglages dans `engine/voice_config.json`. Jamais baisser la
  hauteur artificiellement, jamais de service payant, jamais la voix d'un
  autre créateur.
- ≈ 20 caractères lus par seconde → ≤ 800 caractères lus par épisode.
- Mots mal lus à éviter : « N° » (dire « numéro »), « sweat » (« pull »),
  ville seule en début de phrase, « village », « grésiller », répliques de 3
  mots ou moins, « défi », « fruit », mots d'une syllabe ou en « -illé » en
  fin de phrase (« pain », « grillé »), « revenir », « ne réponds pas » (lu
  « n'en réponds pas » → « ne réponds jamais »). Nombres en lettres ; phrase
  lue différente de l'affichage dans `"voice"`.
- La synthèse est la même d'un essai à l'autre (même phrase = même son) :
  pour corriger, CHANGER la phrase. Tester une tournure douteuse seule
  (`voice.synth` + Whisper medium) avant de relancer un rendu.

## 5. Les étapes de chaque matin

0. Installer : `pip install -q torch==2.6.0 torchaudio==2.6.0 --index-url
   https://download.pytorch.org/whl/cpu`, puis `pip install -q
   chatterbox-tts language_tool_python openai-whisper` (≈ 3 min). Si
   l'installation échoue : ne rien publier, le dire.
1. **Zernio** : `GET /v1/accounts`. Si un compte a `needsReconnection` ou si
   un post de la veille est `failed`, le dire à Fio en premier.
2. **Stats et votes** (`GET /v1/analytics` ; commentaires : `GET
   /v1/inbox/comments/{platformPostId}?accountId=…`) : vues, likes,
   commentaires, partages, temps moyen (`igReelsAvgWatchTime`, ms),
   `completionRate`. Compter les votes A/B de la veille. Tout noter dans
   `series/insights.md` (une section par jour).
3. **Écrire les 4 épisodes** (`episodes/<prefix>-NN.json`, `"style": 2`),
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
6. **Rendu, UN SEUL À LA FOIS**, dans l'ordre des horaires : `python3
   engine/render2.py episodes/<f>.json /tmp/<f>.mp4` (≈ 15 min pour 40 s).
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
    et les nouveaux décors de `engine/render2.py`.
11. **Résumé court en français pour Fio** : les 4 titres, les horaires, les
    réseaux, les votes de la veille, ce que les stats disent (vues, temps
    moyen, complétion) et ce qui change.
