# Routine quotidienne : 3 vidéos par jour

Ce fichier est le mode d'emploi de la routine Claude qui tourne chaque matin.
Objectif : créer 3 épisodes d'une minute et les programmer dans Metricool à
**10:00, 12:00 et 17:00 (Europe/Paris)** le jour même, sans intervention humaine.

## Contexte fixe

- Metricool : brand `blogId` = `7755029`, fuseau `Europe/Paris`.
- Les vidéos sont servies à Metricool depuis la branche **`media`** de ce dépôt :
  `https://raw.githubusercontent.com/diego029929/vid-os-/media/<fichier>.mp4`.
  Metricool copie le fichier chez lui au moment de la programmation, donc à
  chaque exécution les vidéos précédentes sont **supprimées** de la branche
  `media` avant d'ajouter les nouvelles (libère de l'espace).
- On ne commite **jamais** de MP4 sur `main`.
- Moteur : `python3 engine/render.py episodes/epNN.json /chemin/sortie.mp4`
  (environ 6 min par épisode d'une minute).
- Épisodes = fichiers JSON dans `episodes/`. Lire `episodes/ep01.json` comme
  exemple complet du format (scènes, texte, `*mots rouges*`, personnage,
  choix A/B, `record` + `rewind`, bruitages).
- État de la série : `series/state.json`. Plan de la série : fichier indiqué
  dans `series_file`.

## Étapes

1. `getBrandSettings` (Metricool) : noter les réseaux reliés. TikTok toujours ;
   ajouter Instagram (type `REEL`) seulement s'il apparaît dans `networksData`.
2. Lire `series/state.json` et le plan de la série. Écrire les 3 prochains
   épisodes (`episodes/epNN.json`, NN = numéro global sur 2 chiffres ou plus) :
   - durée totale entre **58 et 62 secondes** (somme des `dur`) ;
   - accroche forte dans les 2 premières secondes ;
   - une règle, un choix A/B avec compte à rebours, la mauvaise option jouée
     puis `rewind`, la bonne option, un suspense, puis « ABONNE-TOI POUR LA
     SUITE » et « A OU B ? RÉPONDS EN COMMENTAIRE » ;
   - remplir `title` (≤ 80 caractères, sert de titre TikTok) et `caption`
     (texte du post avec 4 à 6 hashtags) ;
   - garder la continuité (jour, horloge `clock_start`, personnage).
3. **Fin de série** : si `next_episode_in_series` dépasse
   `series_episode_count`, inventer une nouvelle histoire dans le même style
   (personnages bâton, décors soignés, règles, choix A/B) mais avec un autre
   univers : écrire `series/<slug>.md` (même structure que
   `series/apres-la-fin.md`, 7 à 10 épisodes) et mettre à jour `state.json`.
   Il est permis d'ajouter des décors dans `engine/render.py` (nouvelle
   fonction `scene_xxx` + entrée dans `SCENES`) si l'histoire l'exige.
4. Rendre les 3 vidéos dans un dossier temporaire. Pour chacune, vérifier
   avec ffprobe la durée (58–62 s) et faire une planche contact
   (`ffmpeg -vf "fps=1/2.5,scale=216:-1,tile=6x4"`) puis la **regarder** :
   texte lisible, rien de coupé, le texte ne cache pas le visage du personnage, pas de mot avec un astérisque visible.
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
   - `date` / `publicationDate` : aujourd'hui 10:00, 12:00, 17:00 Europe/Paris
     (si un horaire est déjà passé, utiliser le prochain horaire libre et
     décaler) ;
   - `autoPublish: true`, `draft: false` ;
   - `media` : l'URL raw de la branche `media` ;
   - `text` : la `caption` ;
   - `tiktokData` : `{"title": <title>, "privacyOption": "PUBLIC_TO_EVERYONE", "isAigc": true}` ;
   - si Instagram : `instagramData` : `{"type": "REEL", "isAiGenerated": true}`.
   Vérifier dans la réponse que `media` pointe vers `static.metricool.com`.
7. Commiter sur `main` les JSON d'épisodes, `series/state.json` (incrémenter
   les compteurs, ajouter les 3 épisodes à `published`) et les éventuels
   changements du moteur, puis `git push origin main`.
8. En cas d'échec (rendu, push ou Metricool), ne rien publier de bancal :
   s'arrêter et expliquer le problème dans le compte rendu de la session.
