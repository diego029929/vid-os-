# Routine quotidienne (NOUVEAU CONCEPT du 10/11 : « défis »)

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

- **4 vidéos par jour**, TikTok + Instagram (Reel) :
  | Heure (Paris) | 10:00 | 12:00 | 18:00 | 20:00 |
  |---|---|---|---|---|
  | Format | Trouve l'intrus | Quiz | Trouve l'intrus | Quiz |
  (18 h remplace 17 h : meilleur pic d'audience mesuré.)
- Fichiers : `episodes/defi-NNN.json` (numéro global, suivant dans
  `series/state.json` → `defi_next`), rendus avec
  `python3 engine/quiz.py episodes/defi-NNN.json /tmp/defi-NNN.mp4`.
  Le format JSON est expliqué en tête de `engine/quiz.py` ; exemples :
  `episodes/defi-essai-intrus.json`, `defi-essai-quiz.json`,
  `defi-essai-film.json`.

### « Trouve l'intrus » (≈ 22-25 s)
- Une grille d'emojis identiques avec UN emoji différent caché. 3 niveaux, du
  facile au très dur : niveau 1 ≈ 6×7 avec deux emojis bien différents (le
  spectateur gagne → il reste), niveau 2 ≈ 8×10 plus proches, niveau 3 ≈ 9×11
  à 10×13 presque pareils (ex. 😺/🐱, 😀/😃, 🙂/🙃, 🕐/🕑, 🌑/🌚, 💙/💜, 🇫🇷/🇳🇱).
  5 s par niveau (6 s au dernier), puis le cercle rouge « ICI ! ».
- Accroche (`hook`, en haut) : ce qu'il faut trouver, en ≤ 24 caractères.
  `voice_hook` : « Trouve le ... caché. Trois niveaux. Le dernier est vraiment
  dur. » (varier la formule). Ne JAMAIS inventer de faux chiffres (« 99 % des
  gens échouent »).
- Changer de thème chaque jour (animaux, fruits, visages, sport, météo,
  drapeaux, objets…). Vérifier sur la planche que l'intrus du niveau 3 se
  voit quand même en regardant bien.

### « Quiz » (≈ 35-40 s), 5 questions, de la plus facile à la plus dure
- Thèmes qui tournent (un par jour, jamais deux fois de suite) :
  1. Culture G (« si tu as 5/5, t'es très fort ») ;
  2. **Devine le film / dessin animé / chanson en emojis** (`big`) ;
  3. Géographie (capitales, drapeaux en `big`, pays en forme d'emoji) ;
  4. « Vrai ou faux » (2 choix) sur des faits étonnants ;
  5. Nostalgie / années 2000-2010 (dessins animés, jeux, séries connues en France).
- 3 choix par question (2 pour vrai/faux). La bonne réponse change de place.
- **Chaque réponse doit être VRAIE et sans débat** : faits très connus et
  vérifiables. Au moindre doute, vérifier avec WebSearch ou changer de
  question. Une erreur = la vidéo est jetée.
- `voice` : phrase lue (courte, ≤ 12 mots). Pour `big`, lire « Premier
  film, trouve-le vite. » (jamais 3 mots ou moins : la voix les rate). Les choix ne sont pas lus.

### Commun aux deux
- Rien de vide au début : la grille / la question est à l'écran dès la 1re
  image. Fond coloré vif (pas d'horreur, pas de fond blanc).
- Fin (automatique) : « ÉCRIS TON SCORE EN COMMENTAIRE 👇 » + « ABONNE-TOI ».
- Légende (`caption`) : 1re ligne = le défi (« Trouve le chat caché en 5 s
  🐱 »), puis « Écris ton score 👇 », puis 4-5 hashtags qui se cherchent
  (#quiz #trouvelintrus #culturegenerale #devinelefilm #defi #jeu).
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
   Ne juger qu'après 48 h. **Bilan le 14/11** : comparer intrus / quiz (et les
   thèmes de quiz) ; le format qui fait le plus de vues ET de commentaires
   prend plus de créneaux. Si un défi dépasse 2 000 vues, refaire le même
   thème le lendemain (version 2).
3. **Écrire les 4 défis** (`episodes/defi-NNN.json`). Quiz : vérifier chaque
   réponse.
4. Relecture : `python3 engine/check_script.py` ne lit que les épisodes :
   relire soi-même l'orthographe des questions et des choix.
5. **Rendu, UN SEUL À LA FOIS** : `python3 engine/quiz.py
   episodes/defi-NNN.json /tmp/defi-NNN.mp4`.
6. **Contrôles avant publication** :
   - planche contact (`ffmpeg -i v.mp4 -vf "fps=1/1.5,scale=216:-1,tile=6x4"
     -frames:v 1 p.png`) à REGARDER : texte lisible, rien de coupé, cercle
     sur le bon emoji, bonne réponse en vert ;
   - voix : écouter / transcrire (Whisper small, fr) ; mot raté = changer la
     phrase et relancer ;
   - `python3 engine/check_video.py /tmp/defi-NNN.mp4 --min 15 --max 60`
     doit dire OK.
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
   "video_cover_timestamp_ms": 600}, "scheduledFor": "AAAA-MM-JJTHH:MM:SS",
   "timezone": "Europe/Paris"}` (ou `"publishNow": true` si l'heure est
   passée). Vérifier avec `GET /v1/posts/{id}`. Noter `zernio_id` dans
   `series/state.json` → `defis`. Zernio est gratuit (2 comptes, 15 vidéos TikTok /
   24 h). Metricool ne sert plus à publier.
9. **Enregistrer sur main** : les JSON `defi-NNN`, `series/state.json`
   (`defi_next` +4, ajouter les vidéos à `defis` : numéro, format, thème,
   heure, zernio_id), `series/insights.md`.
10. **Résumé court en français pour Fio** : les 4 défis, les horaires, ce
    que les stats disent (vues, temps moyen, commentaires) et ce qui change.
