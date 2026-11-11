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

**11/11 : « Trouve l'intrus » est ARRÊTÉ** (Fio : « c'est vraiment nul » ; la
grille n'occupait que la moitié de l'écran et rien ne se passait). Fio a
demandé à la place **les vidéos de fruits** : petits drames entre fruits qui
parlent (format viral). Ils prennent les créneaux de l'intrus.

- **4 vidéos par jour**, TikTok + Instagram (Reel) :
  | Heure (Paris) | 10:00 | 12:00 | 18:00 | 20:00 |
  |---|---|---|---|---|
  | Format | Les Fruits | Devine en 4 indices | Les Fruits | Quiz |
- Fruits : `episodes/fruits-NNN.json` (suivant dans `series/state.json` →
  `fruits_next`), rendu `python3 engine/fruits.py episodes/fruits-NNN.json
  /tmp/fruits-NNN.mp4` (≈ 10-15 min : voix ≈ 17 s par réplique + images).
  Format JSON expliqué en tête de `engine/fruits.py` ; exemple
  `episodes/fruits-001.json`. Planche des persos : `python3 engine/fruits.py
  --casting /tmp/c.png`.
- Quiz : `episodes/defi-NNN.json` (suivant → `defi_next`), rendu avec
  `python3 engine/quiz.py episodes/defi-NNN.json /tmp/defi-NNN.mp4`.

### « Les Fruits » (≈ 40-55 s), petit drame entre fruits
- 2 ou 3 fruits (14 dispo : pomme, banane, fraise, orange, citron, poire,
  raisin, ananas, pasteque, kiwi, cerise, peche, avocat, tomate), dessinés en
  relief par le moteur, bouche qui bouge avec la voix, gros plan sur celui
  qui parle. Lieux : cuisine, frigo, plage, marche, table.
- Histoire de « télénovela » drôle : tromperie, jalousie, secret, trahison,
  rivalité, mariage, héritage… racontée avec des jeux de mots de fruits
  (« trop acide », « tu me presses », « on n'est pas des pruneaux »).
  Chaque vidéo se comprend seule.
- 11-14 répliques courtes (≤ 12 mots chacune, ≈ 650 caractères en tout).
  **1re réplique = l'accroche** : une accusation ou une révélation choc
  (« Banane ! Pourquoi tu sens la fraise ? »). `hook` en haut (≤ 22 car.).
- Une montée : accusation → mensonge → 3e fruit qui débarque (`"sfx": "dun"`,
  `"shot": "duo"`) → dispute → **chute drôle à la fin** (le couteau
  `"twist": "couteau"`, le mixeur, quelqu'un qui croque, la date de
  péremption…). Varier la chute : pas le couteau 2 jours de suite.
- Fin (`end`) : une question qui fait choisir un camp (« TEAM POMME OU TEAM
  FRAISE ? ») → commentaires.
- **Dès le 12/11 : une série quotidienne, « La Villa des Fruits »** (parodie
  de téléréalité à la française type « La Villa des Cœurs Brisés » /
  « L'Île de la Tentation » ; recherche : series/recherche-11-11.md, les
  succès du genre ont tous un casting fixe et des épisodes numérotés
  presque chaque jour). Ne pas copier le nom d'une émission ou d'une série
  de fruits existante.
  - **Casting FIXE** (toujours mêmes fruits, mêmes voix, mêmes `couleur`) :
    Pommita (pomme, femme1), Banano (banane, homme1), Fraisita (fraise,
    femme2), Kiwito (kiwi, homme2), Citronella (citron, femme3), Ananasso
    (ananas, homme3). Ajouter au plus un nouveau fruit par semaine, avec
    un nom en -ita / -ito / -ella / -o.
  - 2-3 persos par épisode, lieux qui tournent : plage (la villa), cuisine,
    frigo, marche, table.
  - `hook` = « ÉPISODE N » + le choc en ≤ 22 car. (ex. « ÉP. 3 : IL A
    MENTI »). Numéro suivant dans `series/state.json` → `villa_episode`.
  - Fil rouge d'un épisode à l'autre (couples, trahisons, éliminations),
    mais chaque épisode se comprend seul, sans résumé.
  - Fin : **cliffhanger + vote** : `end` = « QUI PART : BANANO OU KIWITO ? ».
    L'épisode suivant suit le vote des commentaires (si moins de 3 votes :
    au hasard).
  - Pas de sexisme, pas de violence réaliste (le couteau de cuisine en gag
    reste rare). Ton qui bascule vite : trahison → gag → larmes.
- Voix : `femme1`, `femme2`, `femme3`, `homme1`, `homme2`, `homme3`, `grave`
  (refs LibriVox dans `assets/ref/`). Deux persos qui se parlent n'ont jamais
  la même voix. Pas de mot seul de 1-2 syllabes en début de réplique
  (« Quoi ? » est sauté par la voix) ; « mon chou » passe.
- Légende : 1re ligne = le drame en une phrase avec emojis fruits, puis
  « Team X ou Team Y ? 👇 », puis `#fruits #drame #humour #histoire #pourtoi`.

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
   Ne juger qu'après 48 h. **Bilan le 14/11** : comparer fruits / quiz (et les
   thèmes de quiz) ; le format qui fait le plus de vues ET de commentaires
   prend plus de créneaux. Si un défi dépasse 2 000 vues, refaire le même
   thème le lendemain (version 2).
3. **Écrire les 2 épisodes Fruits** (`episodes/fruits-NNN.json`) et les 2
   quiz (`episodes/defi-NNN.json`). Quiz : vérifier chaque réponse.
4. Relecture : `python3 engine/check_script.py` ne lit que les épisodes :
   relire soi-même l'orthographe des questions et des choix.
5. **Rendu, UN SEUL À LA FOIS** : `python3 engine/fruits.py
   episodes/fruits-NNN.json /tmp/fruits-NNN.mp4` (≈ 10-15 min) et
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
9. **Enregistrer sur main** : les JSON `defi-NNN` / `fruits-NNN`,
   `series/state.json` (`defi_next` +2, `fruits_next` +2, ajouter les vidéos à `defis` : numéro, format, thème,
   heure, zernio_id), `series/insights.md`.
10. **Résumé court en français pour Fio** : les 4 défis, les horaires, ce
    que les stats disent (vues, temps moyen, commentaires) et ce qui change.
