# Routine quotidienne (version rangée le 10/11)

Ce fichier contient SEULEMENT les règles en vigueur. Il prime sur le message
de la tâche planifiée (qui parle encore de 5 vidéos et de Metricool : il ne
peut pas être modifié). L'historique des essais et des stats est dans
`series/insights.md`.

## 1. Le format (choix de Fio, 10/11)

- **4 séries en parallèle, 1 épisode de chacune par jour**, TikTok +
  Instagram (Reel) :
  | Heure (Paris) | 10:00 | 12:00 | 17:00 | 20:00 |
  |---|---|---|---|---|
  | Vidéo | série n°1 | série n°2 | série n°3 | série n°4 |
- **Séries de 4 épisodes.** Les 4 séries commencent le même jour et finissent
  le même jour, 4 jours plus tard. Le lendemain, 4 NOUVELLES séries
  commencent.
  - Transition : « Le Refuge » (commencée le 10/11) fait 5 épisodes pour
    finir le 14/11. Les 3 autres séries commencent le 11/11 et finissent le
    14/11. 1er cycle complet : du 15/11 au 18/11.
  - Les séries en cours sont dans `series/state.json` → `parallel_series`
    (pour chaque horaire : `slot`, `series`, `series_file`, `episode_count`,
    `next_episode`).
- **Épisode de 85 à 95 s**, forme « Line 9 » (exemple de Fio, voir
  /mnt/project-files/exemples/) :
  1. Histoire en ligne droite : 1 lieu principal, 1-2 personnages, 2-3
     règles. Phrases au présent, avec « tu ».
  2. **Choix A/B UNIQUEMENT à la toute fin** : c'est le vote qui décide la
     partie suivante. Jamais de choix au milieu, ni de `record` /
     `rewind` / « TU ES MORT ».
  3. Chaque règle annoncée est mise à l'épreuve dans le même épisode. Carte
     de règle à l'écran (`"rule": {"n": 1, "text": "..."}`) sur le plan où
     elle est dite et sur celui où elle est testée, jamais sur un gros plan
     visage (on la met sur un plan de dos ou en pied).
  4. Compteur de tension : `counter_label`, `counter_start`, puis `"count":
     N` 2-3 fois.
  5. Lumière : `"mood": "bleu"` au départ, `"rouge"` quand le danger
     apparaît, `"noir"` pour la fin.
  6. Au moins 8 gros plans de visages et 4 plans « objet ».
  7. Fin : cartes A/B, « A : ... B : ... », « LE PLUS DE VOTES DÉCIDE LA
     PARTIE X+1 », puis « ÉCRIS A OU B EN COMMENTAIRE » (à la voix : « ÉCRIS
     TON CHOIX EN COMMENTAIRE »), puis « ABONNE-TOI POUR NE PAS RATER LA
     PARTIE X+1 ». Les deux choix doivent se défendre et chacun a un prix.
  8. Le vote décide vraiment : la partie suivante commence par le choix qui
     a gagné et ses conséquences. Moins de 3 votes = tirage au sort. Noter
     le résultat dans `series/state.json` → `votes`.
  9. Dernier épisode (partie 4) : jamais « fin de la série ». Il finit aussi
     sur un vote.

## 2. Règles d'écriture (Fio)

- **Clair et précis** : chaque réplique se comprend en 2 secondes. Une idée
  par réplique. Dire qui parle (« Léa : ») et qui agit, jamais un « il »,
  « ça » ou « la chose » flou. Dire pourquoi le héros agit.
- Script fluide : chaque phrase découle de la précédente. Jamais de phrase
  coupée sur deux plans. Pas de phrase vide (« la fin va te glacer »).
- **Accroche** : 1re phrase = la situation en moins de 8 mots, au cœur de
  l'action, avec le titre de la série et « PARTIE N » (`subtitle`). Jamais
  la même formule que les épisodes d'avant.
- **Chaque épisode se comprend seul**, sans résumé (« précédemment… »
  interdit). Les personnages, règles et lieux sont présentés dans les 3
  premières lignes, en quelques mots glissés dans l'action.
- Ancrer en France (ville, région) dès le début.
- **S'inspirer de films de NICHE, jamais les recopier** (pas de
  blockbuster : ni Squid Game, ni Saw, ni Ça, ni Scream…). Exemples : Coherence,
  Triangle, Kairo, Noroi, Lake Mungo, The Wailing, Session 9, Absentia, The
  Endless, Calvaire, La Nuée, Dark Water (2002), A Tale of Two Sisters, The
  Void, Lovely Molly. Déjà pris : Pontypool + Ils (Jacques a dit), The
  Ritual + Resolution (Le Refuge). Noter le film en tête du fichier de la
  série.
- Pas de « FICTION » à l'écran, pas de faux journal télé, rien sur une
  catastrophe réelle. Jamais gore. Ne jamais recopier un autre créateur.
- Légende (`caption`) : 1re ligne = la question du vote + « Le plus de votes
  décide la partie X+1 👇 », puis 3 à 5 hashtags dont la ville.
  `title` ≤ 80 caractères, commence par « Partie N · ».

## 3. Les décors (Fio : beaucoup, dessinés, adaptés au script)

- Style DESSINÉ uniquement (le décor `ia` est interdit).
- **Chaque nouvelle série commence par 5 à 7 décors propres** nommés
  `<sigle>_<lieu>` (ex. `jad_*`, `ref_*`), à dessiner dans
  `engine/render2.py` avant l'épisode 1, listés dans le fichier de la série.
  Au moins 3 décors de la série par épisode.
- **Au moins 2 nouveaux décors par épisode**, dessinés selon le script
  (fonction `scene_<lieu>(p)` avant `def scene_old`, ajoutée à `SCENES`).
- **Chaque plan montre ce que dit sa phrase** (« un message » → le
  téléphone, « la porte » → la porte).
- Au moins 7 décors différents par épisode, `flou` sur 1 plan sur 3 au plus.
  Le lieu principal change d'une vidéo à l'autre.
- Vérifier chaque nouveau décor sur une planche AVANT le rendu. Pièges vus le
  10/11 : l'horloge et le compteur cachent les 15 % du haut de l'image (rien
  d'important au-dessus de v ≈ 0.25) ; le texte large est coupé sur les
  côtés (garder u entre 0.2 et 0.8) ; l'ambiance « rouge » rend un décor de
  nuit presque noir.
- `"meteo": "pluie" | "neige" | "cendres"` sur les plans dehors.
- La liste de tous les décors est `SCENES` dans `engine/render2.py`.
  Format des plans : `episodes/essai-style2.json` et l'en-tête de
  `engine/render2.py`.

## 4. La voix (choix de Fio, ne pas changer sans Fio)

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

## 5. Les étapes de chaque matin

0. Installer : `pip install -q torch==2.6.0 torchaudio==2.6.0 --index-url
   https://download.pytorch.org/whl/cpu`, puis `pip install -q
   chatterbox-tts language_tool_python openai-whisper` (≈ 3 min). Si
   l'installation échoue : ne rien publier, le dire.
1. **Zernio** : `GET /v1/accounts`. Si un compte a `needsReconnection` ou si
   un post de la veille est `failed`, le dire à Fio en premier.
2. **Stats et votes** (`GET /v1/analytics` ; commentaires : `GET
   /v1/inbox/comments/{platformPostId}?accountId=…`) : vues, likes,
   commentaires, partages, temps moyen. Ne juger une vidéo qu'après 48 h.
   Compter les votes A/B des 4 vidéos de la veille. Tout noter dans
   `series/insights.md` (une section par jour).
3. **Écrire les 4 épisodes** (`episodes/epNN.json`, `"style": 2`), en
   commençant par celui de 10:00. Nouvelle série : écrire d'abord
   `series/<slug>.md` (film source, univers, règles, personnages, décors,
   tableau des 4 épisodes) et dessiner ses décors.
4. **Test du spectateur extérieur, obligatoire** : écrire les répliques lues
   (une par ligne) dans un fichier texte, puis lancer un agent neuf (outil
   Agent, sans autre contexte) qui joue un spectateur TikTok de 16-25 ans
   n'ayant rien vu. Il donne : résumé en 3 phrases, lignes où il est perdu,
   si les deux choix se défendent, clarté /10, envie de la suite /10.
   Corriger et refaire tant que la clarté est < 8. Noter les notes dans
   `insights.md`.
5. Relecture : `python3 engine/check_script.py episodes/epNN.json` (corriger
   les « FAUTE »).
6. **Rendu, UN SEUL À LA FOIS** (sinon la mémoire sature), dans l'ordre des
   horaires : `python3 engine/render2.py episodes/epNN.json /tmp/epNN.mp4`
   (≈ 35 min). Le lancer dès que le script est prêt. Vérifier avec `pgrep`
   qu'aucun autre rendu ne tourne.
7. **Contrôles avant publication** :
   - planche contact (`ffmpeg -vf "fps=1/2.5,scale=216:-1,tile=6x7"`) à
     REGARDER : texte lisible, rien de coupé, chaque plan montre sa phrase ;
   - voix : transcription Whisper (modèle small, fr) comparée au texte. Un
     mot répété, bégayé ou incompréhensible = réécrire la réplique (plus
     courte, mots simples) et relancer. Whisper se trompe souvent : réécouter
     le passage douteux en découpant 2-3 s avec ffmpeg avant de relancer ;
   - `python3 engine/check_video.py /tmp/epNN.mp4` doit dire OK (durée, son
     à -14 LUFS, pas d'écran noir, 1re image ni blanche ni noire).
   Ne jamais publier une vidéo défectueuse.
8. **Branche `media`** (jamais de push forcé, jamais de MP4 sur main) :
   `git worktree add /tmp/media media` (ne PAS faire `git checkout media`
   pendant un rendu), supprimer les vidéos de la veille déjà publiées,
   copier la nouvelle, commit, `git push origin media`.
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
   "video_cover_timestamp_ms": 600}, "scheduledFor": "AAAA-MM-JJTHH:MM:SS",
   "timezone": "Europe/Paris"}` (ou `"publishNow": true` si l'heure est
   passée). Vérifier avec `GET /v1/posts/{id}`. Noter `zernio_id` dans
   `series/state.json`. Zernio est gratuit (2 comptes, 15 vidéos TikTok /
   24 h). Metricool ne sert plus à publier.
10. **Enregistrer sur main** : les JSON d'épisodes, les fichiers de série,
    `series/state.json` (`parallel_series` : avancer `next_episode`,
    ajouter les vidéos à `published`), `series/insights.md` et les nouveaux
    décors de `engine/render2.py`.
11. **Résumé court en français pour Fio** : les 4 titres, les horaires, les
    réseaux, les votes de la veille et ce que les stats ont fait changer.
