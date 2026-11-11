# Routine quotidienne (depuis le 12/11 : « Les Fruits » 10h + 18h, « Devine en 4 indices » 12h, Quiz 20h)

Ce fichier contient SEULEMENT les règles en vigueur. Il prime sur le message
de la tâche planifiée (qui parle encore de 5 vidéos, de séries et de
Metricool : il ne peut pas être modifié). L'historique est dans
`series/insights.md`.

## 0. Pourquoi on a changé (10/11, carte blanche de Fio)

Fio : « ça perce pas, fais ce que tu veux, juste des choses qui marchent ».
Les stats Zernio de 82 posts disent : TOUTES les vidéos TikTok plafonnent à
≈ 750-900 vues (le premier lot que TikTok donne à chaque vidéo), puis ≈ 250
depuis le 09/11. Aucune n'a été poussée plus loin, car les gens partent vite :
temps moyen 6-14 s sur des vidéos de 90 s (1 à 8 % vont au bout), et presque
aucun commentaire. Les séries d'horreur, les votes A/B et les courtes
« SURVIS ? » sont donc ARRÊTÉS (« Le Refuge » s'arrête à la partie 1).

Nouveau concept : **des défis courts (20-40 s) où on joue en regardant**. Le
spectateur reste jusqu'à la réponse, revoit la vidéo s'il a raté (TikTok
compte les revisionnages), et commente son score (« 4/5 », « trouvé en 2 s »).
C'est un format qui marche en France sur les comptes sans visage, il se
fabrique en entier ici, gratuitement, et le rendu prend 1-3 min (au lieu de 35).

**Permission de Fio (10/11 soir)** : Claude peut changer de concept ou de
format SANS demander à Fio, quand les stats le justifient (après 48 h de
recul et au moins 3 jours de test). Faire le changement ici (ROUTINE.md +
moteur), puis l'expliquer à Fio en quelques lignes dans le résumé.

## 1. Le format

**11/11 soir : FILMS DE FRUITS (modèle envoyé par Fio).** Fio : « t'as pas
compris sur les vidéos de fruit », avec une vidéo exemple (Dropbox, « Vidéo
11-11-2026 19 05 32.mp4 », compte @fruits_enrouelibre). Le format, ce sont
des **petits films** : humains réalistes (corps, vêtements) avec une **tête
de fruit**, dans de **vrais décors** (rue de Paris, banque, bureau, villa),
une **histoire à idée forte** (exemple : « dans un monde où personne ne sait
mentir, Dylan découvre qu'il peut mentir » → argent, voiture, PDG, villa →
« flash spécial : quelqu'un ment » → la police frappe → « À SUIVRE… »),
**un plan par réplique** (≈ 2-3 s), sous-titres 1-3 mots, ≈ 60-100 s.
Les fruits dessinés en cuisine (`engine/fruits.py` seul, `fruits-001`) et
« La Villa des Fruits » sont ABANDONNÉS (pas le format voulu). « Trouve
l'intrus » est arrêté aussi.

- **4 vidéos par jour**, TikTok + Instagram (Reel) :
  | Heure (Paris) | 10:00 | 12:00 | 18:00 | 20:00 |
  |---|---|---|---|---|
  | Format | Film de fruits | Devine en 4 indices | Film de fruits | Quiz |
- Films : `episodes/film-NNN.json` (suivant → `series/state.json` →
  `film_next`), format JSON en tête de `engine/film.py`, exemple
  `episodes/film-001.json`. Deux étapes :
  1. images : `/tmp/sdenv/bin/python engine/film_images.py
     episodes/film-NNN.json /tmp/film-NNN-img` (SDXL-Turbo, gratuit, sur CPU,
     ≈ 50 s par plan, ≈ 15-20 min pour 15 plans) ;
  2. vidéo : `python3 engine/film.py episodes/film-NNN.json /tmp/film-NNN-img
     /tmp/film-NNN.mp4` (voix + têtes de fruit + montage, ≈ 10 min).
  Le venv : `python3 -m venv /tmp/sdenv && /tmp/sdenv/bin/pip install -q
  torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu &&
  /tmp/sdenv/bin/pip install -q diffusers transformers accelerate
  "opencv-python-headless<5"` (séparé, car diffusers casse le transformers
  de Chatterbox). 1er lancement : téléchargement du modèle (≈ 7 Go, 1 min).
- Quiz : `episodes/defi-NNN.json` (suivant → `defi_next`), rendu avec
  `python3 engine/quiz.py episodes/defi-NNN.json /tmp/defi-NNN.mp4`.

### « Film de fruits » (10h + 18h, ≈ 45-90 s)
- **Idée forte en une phrase**, inspirée d'un film à concept (« et si… ») :
  quelqu'un qui ne peut pas mentir / qui peut mentir, qui reçoit des SMS de
  demain, qui revit la même journée, qui entend les pensées, qui gagne tout
  ce qu'il touche, un monde où l'argent n'existe pas… Histoire ORIGINALE,
  jamais la copie du film ni de la vidéo de @fruits_enrouelibre.
- Structure : accroche choc au 1er plan (`hook` en haut, ≤ 26 car.) → le
  héros découvre son pouvoir → escalade rapide et drôle (argent, voiture,
  promotion, villa…) → retournement (flash spécial, police, message
  inquiétant) → cliffhanger + `end` « À SUIVRE… » (+ `end_sub` question pour
  les commentaires). Les épisodes suivants reprennent le même héros (série).
- 12-20 plans, **une réplique courte par plan** (≤ 12 mots), un lieu
  différent tous les 2-3 plans. Plan sans perso : `"off": true` (voix hors
  champ, ex. derrière une porte). `banner` pour un bandeau (« FLASH SPÉCIAL »).
- Casting : le héros + 2-4 persos, chacun un fruit (`fruit` = un des 14 de
  `engine/fruits.py`), une voix (`femme1-3`, `homme1-3`, `grave`) et un
  `look` en anglais TOUJOURS identique (âge, cheveux, vêtements) pour qu'on
  le reconnaisse d'un plan à l'autre. `lieu` et `action` en anglais.
- Contrôle des images (planche des `shot-XX.png`) : UN seul perso par image,
  tête de fruit bien posée (ni cheveux ni 2e tête visibles). Sinon : retirer
  le plan de `faces.json`, changer son `seed` dans le JSON, relancer l'étape 1
  (elle ne refait que les plans manquants).
- Légende : la prémisse en une phrase + emojis, la question, puis
  `#fruits #histoire #film #suspense #pourtoi`.

### 11/11 : « Devine le film en emojis » ARRÊTÉ (Fio : « nul »)
86 vues, 6 s regardées sur 50 s. Les recherches (voir
`series/recherche-11-11.md`) expliquent pourquoi : image figée pendant le
compte à rebours, rébus soit évident soit impossible, voix qui lit la
consigne, vidéo trop longue, format usé. Ne plus faire de rébus d'emojis
(film, chanson, dessin animé).

### « Devine en 4 indices » (12h, ≈ 18 s), UN seul objet à deviner
Ce qui marche chez les comptes de devinettes qui percent (« tu l'as trouvé à
quel indice ? ») : une image qui se révèle petit à petit, ça bouge tout le
temps, c'est court, et chacun commente un chiffre.
- `"type": "indices"` dans `episodes/defi-NNN.json` (format en tête de
  `engine/quiz.py`). Une manche (`rounds` = 1 élément) : 1 emoji (animal,
  pays/drapeau, objet, aliment, monument), sa réponse (`answer`, ≤ 16 car.,
  ex. « LA GIRAFE »), 4 indices du plus vague au plus évident (≤ 28 car.
  chacun). Le moteur pixelise l'image (très flou → net), tic-tac, ding.
- **Pas de voix** (les comptes qui percent n'en ont pas, et ça raccourcit).
- L'indice 1 doit être vrai mais vague (« Je vis en Afrique »), l'indice 4
  donne presque la réponse. Faits vérifiables uniquement (WebSearch au
  moindre doute). L'emoji doit être reconnaissable une fois net.
- Thèmes qui tournent : animal, pays (drapeau 🇯🇵 etc.), métier/objet,
  aliment/plat, personnage historique via un objet (👑 + indices).
- `hook` : « DEVINE L'ANIMAL », « DEVINE LE PAYS »… `end` : « TROUVÉ À QUEL
  INDICE ? ». Légende : « 90 % ne trouvent pas avant l'indice 3 🤔 », puis
  « Écris ton indice 👇 », puis `#devinette #quiz #defi #animaux #pourtoi`.
- Titre fixe numéroté pour créer un rendez-vous : « Devine en 4 indices #N ».

### « Quiz » (20h, ≈ 25-30 s), 5 questions, de la plus facile à la plus dure
- **Plus court qu'avant** (les quiz qui percent font 3-5 s par question) :
  pas de `voice_hook` (la 1re question arrive à 0 s), `voice` ≤ 8 mots,
  `"seconds": 3`.
- Thèmes qui tournent (un par jour, jamais deux fois de suite) :
  1. Culture G (« si tu as 5/5, t'es très fort ») ;
  2. Géographie (capitales, drapeaux en `big`) ;
  3. « Vrai ou faux » (2 choix) sur des faits étonnants ;
  4. Nostalgie / années 2000-2010 (dessins animés, jeux, séries connues en France).
  (Plus de « devine le film en emojis ».)
- 3 choix par question (2 pour vrai/faux). La bonne réponse change de place.
- **Chaque réponse doit être VRAIE et sans débat** : faits très connus et
  vérifiables. Au moindre doute, vérifier avec WebSearch ou changer de
  question. Une erreur = la vidéo est jetée.
- `voice` : phrase lue (courte, ≤ 8 mots ; jamais 3 mots ou moins : la voix
  les rate). Les choix ne sont pas lus.

### Commun aux quiz
- Rien de vide au début : la question est à l'écran dès la 1re
  image. Fond coloré vif (pas d'horreur, pas de fond blanc).
- Fin (automatique) : « ÉCRIS TON SCORE EN COMMENTAIRE 👇 » + « ABONNE-TOI ».
- Légende (`caption`) : 1re ligne = le défi (« 5 questions de culture G 🧠 »),
  puis « Écris ton score 👇 », puis 4-5 hashtags qui se cherchent
  (#quiz #culturegenerale #devinelefilm #defi #jeu).
  `title` ≤ 80 caractères.
- **Répondre aux commentaires** (Zernio inbox) n'est pas automatisé : ne pas
  le faire.

## 2. La voix (choix de Fio, ne pas changer sans Fio)

- Chatterbox + `assets/ref/ref-narrateur-grave.wav` (« voix 1 », homme grave
  naturel, choisie le 09/11). Réglages dans `engine/voice_config.json`.
  Jamais baisser la hauteur artificiellement, jamais de service payant,
  jamais la voix d'un autre créateur.
- Repère : ≈ 20 caractères lus par seconde → un épisode fait ≤ 1 750
  caractères lus.
- Mots mal lus à éviter : « N° » (dire « numéro »), « sweat » (« pull »),
  ville seule en début de phrase, « village », « grésiller », répliques de 3
  mots ou moins, « personne ne frappe plus », « le feu meurt ». Écrire les
  nombres en lettres en cas de doute, ou mettre la phrase lue dans
  `"voice"`.
- Pour les défis, la voix ne dit que des phrases courtes : rendu ≈ 1-3 min.
  Si Chatterbox ne s'installe pas, publier quand même SANS voix
  (`QUIZ_VOICE=0`) plutôt que rien : la musique et le « ding » suffisent.

## 3. Les étapes de chaque matin

0. Installer : `pip install -q torch==2.6.0 torchaudio==2.6.0 --index-url
   https://download.pytorch.org/whl/cpu`, puis `pip install -q
   chatterbox-tts openai-whisper` (≈ 3 min). Police emoji : si
   `/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf` manque,
   `apt-get install -y fonts-noto-color-emoji`.
1. **Zernio** : `GET /v1/accounts`. Si un compte a `needsReconnection` ou si
   un post de la veille est `failed`, le dire à Fio en premier.
2. **Stats** (`GET /v1/analytics`) : pour chaque vidéo, vues, likes,
   commentaires, partages, temps moyen (`igReelsAvgWatchTime`, en ms) et
   `completionRate`. Noter dans `series/insights.md` (une section par jour).
   Ne juger qu'après 48 h. **Bilan le 14/11** : comparer films de fruits / quiz (et les
   thèmes de quiz) ; le format qui fait le plus de vues ET de commentaires
   prend plus de créneaux. Si un défi dépasse 2 000 vues, refaire le même
   thème le lendemain (version 2).
3. **Écrire les 2 films de fruits** (`episodes/film-NNN.json`) et les 2
   quiz (`episodes/defi-NNN.json`). Quiz : vérifier chaque réponse.
4. Relecture : `python3 engine/check_script.py` ne lit que les épisodes :
   relire soi-même l'orthographe des questions et des choix.
5. **Rendu, UN SEUL À LA FOIS** : films (images puis vidéo, voir § 1,
   ≈ 30 min chacun ; commencer par eux) et
   `python3 engine/quiz.py episodes/defi-NNN.json /tmp/defi-NNN.mp4`.
6. **Contrôles avant publication** :
   - planche contact (`ffmpeg -i v.mp4 -vf "fps=1/1.5,scale=216:-1,tile=6x4"
     -frames:v 1 p.png`) à REGARDER : texte lisible, rien de coupé, bonne
     réponse en vert (quiz), visages et gros plans corrects (fruits) ;
   - voix : écouter / transcrire (Whisper small, fr) ; mot raté = changer la
     phrase et relancer ;
   - `python3 engine/check_video.py /tmp/defi-NNN.mp4 --min 15 --max 60`
     doit dire OK. Le moteur sort ≈ -17 LUFS : normaliser avant (`ffmpeg -i in.mp4
     -c:v copy -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 192k out.mp4`).
   - Phrases que la voix rate : « défi » (lu « déchi »), « fruit », une
     question qui finit par « la Joconde » / « du monde » (bruit après).
   Ne jamais publier une vidéo défectueuse.
7. **Branche `media`** (jamais de push forcé, jamais de MP4 sur main) :
   `git worktree add /tmp/media media`, supprimer les vidéos déjà publiées,
   copier les nouvelles, commit, `git push origin media`.
8. **Programmer dans Zernio** dès que la vidéo est prête :
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
   `series/state.json` → `defis`. Zernio est gratuit (2 comptes, 15 vidéos TikTok /
   24 h). Metricool ne sert plus à publier.
9. **Enregistrer sur main** : les JSON `defi-NNN` / `film-NNN`,
   `series/state.json` (`defi_next` +2, `film_next` +2, ajouter les vidéos à `defis` : numéro, format, thème,
   heure, zernio_id), `series/insights.md`.
10. **Résumé court en français pour Fio** : les 4 défis, les horaires, ce
    que les stats disent (vues, temps moyen, commentaires) et ce qui change.
