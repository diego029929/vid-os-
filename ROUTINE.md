# Routine quotidienne (depuis le 14/11 : « Bataille de pays » 10h + 18h, « Tu préfères » 12h + 20h)

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

## 1. Le format (depuis le 14/11 : « Tu préfères » + « Bataille de pays »)

**14/11 nuit : grande recherche** (4 recherches web en parallèle + 3 essais
vidéo ; synthèse dans `series/recherche-14-11.md`). Pourquoi on bloque à
≈ 250-300 vues : rétention trop faible et rien qui donne envie de commenter
ou d'envoyer à un ami ; et on a changé de concept tous les 2 jours, donc
aucun format n'a eu le temps d'être jugé. Ce n'est pas l'API ni le compte.
Deux formats qui ont des preuves en France et se font à 100 % ici :

- **4 vidéos par jour**, TikTok + Instagram (Reel) :
  | Heure (Paris) | 10:00 | 12:00 | 18:00 | 20:00 |
  |---|---|---|---|---|
  | Format | Bataille de pays | Tu préfères | Bataille de pays | Tu préfères |
- **On garde ces 2 formats au moins jusqu'au 28/11** (2 semaines, ≈ 28
  vidéos) avant de juger. Ne PAS changer de concept avant, sauf demande de
  Fio. Au bout de 7 jours, le format qui a le plus de vues + commentaires +
  partages peut prendre 3 créneaux sur 4.
- Suivants : `series/state.json` → `tp_next` (fichiers
  `episodes/tp-NNN.json`) et `bataille_next` (`episodes/bataille-NNN.json`).

### « Tu préfères 🔴 ou 🔵 ? » (12h + 20h, ≈ 60 s)
Modèle : @tu.prefere.quoii6 (281 k abonnés, médiane ≈ 680 000 vues en
2026). Écran coupé rouge/bleu, la voix lit « Tu préfères A, ou B ? », 3-2-1,
pourcentages qui se remplissent, dilemme suivant. Personne ne se sent bête
(pas de bonne réponse), on se compare aux %, on commente son score.
- Rendu : `python3 engine/tupreferes.py episodes/tp-NNN.json /tmp/tp-NNN.mp4`
  (≈ 4-6 min). Format JSON en tête du moteur, exemple `episodes/tp-001.json`.
- **7 dilemmes**, un **thème par vidéo** (`theme` ≤ 12 car. : « bouffe »,
  « pouvoirs », « argent », « école », « vacances », « jeux vidéo », « amour »,
  « animaux », « films », « métiers », « Noël »…), jamais le même deux fois
  de suite. Dilemmes vraiment durs à choisir (deux options tentantes OU deux
  galères), concrets, compris en 1 s, pour ados/jeunes adultes français.
- Chaque option : texte ≤ 34 car. + UN emoji qui la montre exactement. Les
  deux emojis doivent être différents et lisibles (tester qu'ils
  s'affichent : le moteur s'arrête sinon).
- **2 options-pièges** par vidéo (c'est ce qui fait commenter/partager) :
  au 4e dilemme une option « commenter … » (ex. « Commenter ton plat
  préféré » vs une galère), au 7e « Envoyer cette vidéo à ton meilleur
  pote » vs une galère drôle.
- `pa` = % estimé pour l'option rouge (écrit petit « estimation » à
  l'écran) : être réaliste, éviter 50, varier (de 9 à 91).
- Voix : `voice` facultatif (phrase complète lue), sinon « Tu préfères a, ou
  b ? ». Nombres en lettres dans `voice`. `hook` (lu à 0 s, ≤ 8 mots) et
  `hook_text` (≤ 18 car.) changent à chaque vidéo (« T'as bon goût ? », « Les
  pires choix », « Choix impossible »…). `end_voice` / `end` : « T'as eu
  combien de rouges ? ».
- Légende : « Tu préfères… ? (thème) 🔴🔵 », puis « T'as eu combien de 🔴 ?
  Dis-le en commentaire 👇 », puis `#tupreferes #choix #jeu #wouldyourather
  #pourtoi`. Titre : « Tu préfères… #N (thème) ».

### « Bataille de pays » (10h + 18h, ≈ 30-45 s, sans voix)
Simulation physique : des billes-drapeaux rebondissent dans un anneau qui
tourne ; une bille qui sort par l'ouverture est éliminée (bandeau
« MAROC ÉLIMINÉ (13e) »), la dernière gagne. Chaque rebond joue la note
suivante d'une mélodie du domaine public (`ode`, `elise`, `jacques`,
`clair`). Modèles : @elitemarbleclash (404 k vues avec 7,9 k abonnés),
simulations de balles musicales (2 à 37 M de vues) ; en français la place
est presque libre. Les gens soutiennent leur pays dans les commentaires.
- Rendu : `python3 engine/bataille.py episodes/bataille-NNN.json
  /tmp/bataille-NNN.mp4` (≈ 1 min, cherche tout seul une graine qui donne
  ≈ 28-45 s avec une finale serrée). Exemple `episodes/bataille-001.json`.
- **Varier chaque vidéo** (TikTok/Instagram pénalisent le contenu
  répétitif) : la liste de pays (12-16), le `title` (« 16 PAYS, 1 SEUL
  SURVIVANT », « QUEL PAYS D'AFRIQUE GAGNE ? », « EUROPE : QUI SURVIT ? »,
  « LA FRANCOPHONIE SE BAT »…), la mélodie, `colors` (2 couleurs du fond),
  `ring` (couleur de l'anneau). Toujours plusieurs pays très présents chez
  les Français (France, Maroc, Algérie, Tunisie, Sénégal, Côte d'Ivoire,
  Belgique, Suisse, Canada, Portugal, Espagne, Italie, Cameroun, RD Congo,
  Haïti…). `"f": true` pour un nom féminin (« ÉLIMINÉE »).
- Le gagnant est le hasard de la physique : ne jamais truquer.
- `subtitle` change aussi (« CHOISIS TON PAYS AVANT QUE ÇA COMMENCE »,
  « COMMENTE TON PAYS », « TON PAYS VA-T-IL SURVIVRE ? »).
- Légende : « Quel pays va survivre ? 🌍 », puis « Commente ton pays 👇 »,
  puis `#pays #drapeaux #simulation #satisfying #pourtoi`.
- Éviter toute politique ou insulte dans les textes ; c'est un jeu.

### Formats ARRÊTÉS (ne plus faire)
Séries d'horreur + votes A/B + SURVIS (10/11), « Trouve l'intrus » (11/11,
Fio : « vraiment nul »), « Devine le film en emojis » (11/11, Fio : « nul »),
films de fruits (11/11, Fio : « horribles », suspendus), quiz 5 questions et
« Devine en 4 indices » (14/11 : plafond 260-310 vues malgré 4 jours ; les
moteurs `engine/quiz.py`, `engine/film.py` restent dans le dépôt).
« Histoire vraie en 45 s » (`engine/histoire.py`) a été essayé le 14/11 mais
pas retenu : les images Wikimedia sont souvent bloquées (erreur 429) et
chaque fait doit être vérifié.

### Commun aux 2 formats
- Rien de vide au début : le 1er dilemme / l'anneau qui tourne est à
  l'écran dès la 1re image (pas d'intro, pas de fond blanc).
- `title` ≤ 80 caractères. **Répondre aux commentaires** (Zernio inbox)
  n'est pas automatisé : ne pas le faire.

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
- « Tu préfères » utilise la même voix 1 (défaut de `voice_config.json`).
  Une voix plus vive (`"ref": "ref-pierre-moyen.wav"` dans le JSON) a été
  essayée le 14/11 : ne l'utiliser que si Fio la choisit.
- « Bataille de pays » n'a pas de voix. Si Chatterbox ne s'installe pas,
  publier quand même les 2 batailles.

## 3. Les étapes de chaque matin

0. Installer : `pip install -q torch==2.6.0 torchaudio==2.6.0 --index-url
   https://download.pytorch.org/whl/cpu`, puis `pip install -q
   chatterbox-tts openai-whisper` (≈ 3 min). Police emoji : si
   `/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf` manque,
   `apt-get install -y fonts-noto-color-emoji`. Et `pip install -q pymunk`
   (physique de « Bataille de pays »).
1. **Zernio** : `GET /v1/accounts`. Si un compte a `needsReconnection` ou si
   un post de la veille est `failed`, le dire à Fio en premier.
2. **Stats** (`GET /v1/analytics`) : pour chaque vidéo, vues, likes,
   commentaires, partages, temps moyen (`igReelsAvgWatchTime`, en ms) et
   `completionRate`. Noter dans `series/insights.md` (une section par jour).
   Ne juger qu'après 48 h. Comparer « Tu préfères » et « Bataille de
   pays » (vues, temps moyen, complétion, commentaires, partages). Pas de
   changement de concept avant le 28/11 (voir § 1). Si une vidéo dépasse
   2 000 vues, refaire le même thème / la même liste de pays le lendemain.
   Lire aussi les commentaires des batailles : les pays demandés entrent
   dans la bataille suivante (« vous l'avez demandé »).
3. **Écrire les 4 vidéos** : 2 batailles (`episodes/bataille-NNN.json`,
   listes de pays différentes) + 2 « Tu préfères » (`episodes/tp-NNN.json`,
   thèmes différents). Si les fichiers du jour existent déjà (préparés
   d'avance), les utiliser tels quels.
4. Relecture : relire soi-même l'orthographe des dilemmes et des noms de pays.
5. **Rendu, UN SEUL À LA FOIS** : `python3 engine/bataille.py
   episodes/bataille-NNN.json /tmp/bataille-NNN.mp4` (≈ 1 min) et
   `python3 engine/tupreferes.py episodes/tp-NNN.json /tmp/tp-NNN.mp4`
   (≈ 4-6 min). Les deux moteurs normalisent déjà le son (-14 LUFS).
6. **Contrôles avant publication** :
   - planche contact (`ffmpeg -i v.mp4 -vf "fps=1/1.5,scale=216:-1,tile=6x4"
     -frames:v 1 p.png`) à REGARDER : texte lisible, rien de coupé, emojis
     et drapeaux affichés, pourcentages lisibles ;
   - voix : écouter / transcrire (Whisper small, fr) ; mot raté = changer la
     phrase et relancer ;
   - `python3 engine/check_video.py /tmp/xxx.mp4 --min 20 --max 75`
     doit dire OK.
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
9. **Enregistrer sur main** : les JSON `bataille-NNN` / `tp-NNN`,
   `series/state.json` (`bataille_next` +2, `tp_next` +2, ajouter les vidéos
   à `defis` : numéro, format, thème/pays, heure, zernio_id, et pour les
   batailles le gagnant + la graine), `series/insights.md`.
10. **Résumé court en français pour Fio** : les 4 vidéos, les horaires, ce
    que les stats disent (vues, temps moyen, commentaires) et ce qui change.
