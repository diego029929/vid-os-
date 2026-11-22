# Routine quotidienne (depuis le 22/11 : ROTATION pilotée par les stats, `engine/plan.py`, style « Nuit & téléphone »)

> **NOUVEAU 15/11 au soir (choix de Fio) : toutes les vidéos se font dans le
> style « Nuit & téléphone »** avec `engine/nuit.py` (voir § 1 bis), y compris
> les parties 2 et 3 des 4 séries en cours (mêmes histoires, nouveau dessin).
> `engine/render2.py` (style 2) n'est plus utilisé pour publier.

> **NOUVEAU 21/11 (Fio : « tu publies tout le temps la même chose, c'est chiant, fais évoluer
> les vidéos comme tu le calcules pour les follows ») : § 0 bis passe AVANT tout le reste.**
> Fini les 4 séries identiques par jour : chaque matin `engine/plan.py` décide, à partir des stats,
> le format, l'ambiance et l'accroche de CHAQUE créneau. La routine suit ce plan.

## 0 bis. Rotation pilotée par les stats (OBLIGATOIRE, dès le 22/11)

1. Après les stats (§ 5, étape 2), lancer **`python3 engine/plan.py AAAA-MM-JJ`** (date du jour).
   Il lit Zernio, note chaque vidéo (abonnés gagnés pour 1 000 vues 35 %, rétention = temps moyen /
   durée 25 %, likes 20 %, commentaires + partages + enregistrements 10 %, vues 10 %), puis écrit
   `series/plans/AAAA-MM-JJ.json` (et l'affiche). **Suivre ce plan créneau par créneau** : `format`,
   `ambiance`, `accroche`, `duree`. Ne pas le « corriger » à la main, sauf demande de Fio ou format
   impossible (le dire dans le résumé).
2. Les règles que le plan applique (ne pas les contourner) :
   - **jamais plus de 2 séries en même temps** ; les autres séries s'arrêtent (`series_arretees`) :
     les retirer de `parallel_series` (les garder dans `previous_parallel_series` avec
     `"arretee": "AAAA-MM-JJ"`). Si quelqu'un réclame la suite en commentaire, sa fin pourra revenir
     plus tard en format `histoire` ;
   - **1 à 2 nouveautés par jour** (format, ambiance ou accroche pas encore notés) ;
   - **coupe** 7 jours ce qui est dans le tiers du bas après ≥ 4 vidéos (format) ou ≥ 3 (ambiance,
     accroche) → `state.json` → `variation.coupes` ; ensuite c'est re-testé ;
   - **jamais 2 créneaux du même format le même jour** (sauf 2 séries), jamais la même ambiance ni la
     même accroche deux fois le même jour, et on évite celles de la veille ;
   - les formats `interdit` de `series/formats.json` (jugés nuls par Fio) ne reviennent JAMAIS.
3. **Les formats** (`series/formats.json`, modèles testés dans `episodes/modeles/`, à copier) — tous
   avec `engine/nuit.py` sauf `edit` :
   | format | durée | forme | modèle |
   |---|---|---|---|
   | `serie` | 30-40 s | 3 parties, vote 1/2 (§ 1) | `episodes/exemple-nuit.json` |
   | `histoire` | 25-35 s | histoire COMPLÈTE, chute au dernier plan, pas de vote. Légende : « T'aurais fait quoi ? 👇 » | `modeles/histoire.json` |
   | `sms` | 25-40 s | ≥ 70 % de plans `tel` (sms, appel, notif, photo, localiser) : on lit la conversation | `modeles/sms.json` |
   | `regles` | 30-42 s | « Les 4-5 règles de… », carte `regle` puis 1 plan qui la montre ; fin « Laquelle tu briserais en premier ? Écris le numéro. » | `modeles/regles.json` |
   | `pov` | 12-20 s | 5-7 plans, une seule peur, le dernier plan = le premier (la vidéo boucle) | `modeles/pov.json` |
   | `edit` | 15-20 s | edit GTA 6, 8h et 9h (§ 1 ter) | `gta6-edit-02.json` |
   Un épisode d'un nouveau format = même qualité que les séries : § 2 (clarté), test du spectateur
   (§ 5 étape 4), vérification de la voix, planche. Le titre ne commence par « Partie N · » QUE pour
   `serie`. Le `etiquette` de l'horloge = le format (« HISTOIRE », « MESSAGES », « RÈGLES », « POV »).
4. **Ambiance** = champ `"ambiance"` en tête du JSON (`nuit`, `rouge`, `vert`, `bleu`, `sepia`, `nb`,
   `vhs` ; aperçu : `/mnt/project-files/rotation/ambiances.png`). Elle teinte les décors et objets ;
   téléphone, règle et choix restent nets. Une série garde la même ambiance dans toutes ses parties.
   Choisir des décors qui vont avec (`vert` → hôpital/forêt, `bleu` → mer/neige, `sepia` → maison
   ancienne/cassette…).
5. **Accroche** = champ `"accroche"` = type du 1er plan + 1re phrase (liste dans
   `series/formats.json` → `accroches`). Le 1er plan DOIT correspondre au type choisi.
6. **Toujours écrire les 3 champs** `"format"`, `"ambiance"`, `"accroche"` dans le JSON de l'épisode
   ET dans l'entrée `published` de `series/state.json` : sans eux, `plan.py` ne peut pas apprendre.
7. **Légendes variées** : pas deux fois la même formule le même jour (question du vote pour `serie`,
   « T'aurais fait quoi ? » / « Tu l'as vu ? » / « Laquelle tu briserais ? » pour les autres), et
   hashtags tournants (`#horreur` + 2-3 parmi `#histoire #creepy #pov #sms #frissons #peur
   #histoiredhorreur #nuit #pourtoi #fyp`). Les vidéos trop semblables se font bloquer par TikTok
   (Coupure p2, Ferry p2, Voisin p1 : 5-12 vues).
8. Dans le résumé à Fio (§ 5 étape 11) : une ligne « ce qui change aujourd'hui » (les nouveautés
   testées, ce qui est gardé, ce qui est coupé, avec le chiffre qui le justifie).

## 0 quater. Ce que font les vidéos à millions de vues (recherche du 22/11, `series/recherche-22-11.md`)

> Fio, 22/11 : « ça pue… base-toi sur de vrais exemples de vidéos qui ont fait des millions de vues ».
> Ces règles passent AVANT § 0 bis et § 0 ter quand elles se contredisent.

1. **Une vidéo = une histoire COMPLÈTE de 25 à 32 s** (Zack D. Films 253 M de vues en 31 s ;
   Jake Fellman 88 M, vidéos de 30 s vues à 85 % ; Broken Finger Paradise 30 s). La question est posée à
   la 1re seconde et la réponse arrive à la dernière, puis la vidéo boucle. **1 seule série à la fois**
   (plan.py : `MAX_SERIES = 1`) ; nos parties 2 et 3 décrochent (on n'a pas vu la partie 1).
2. **Accroche = situation normale + UN détail impossible, en une phrase** (« Mon copain dort sur mes
   genoux… alors qui m'envoie des messages ? », histoire SMS virale). Le `texte_accroche` ET la 1re
   image montrent ce détail. Jamais une phrase de mise en place (« Tu emménages à Lille… ») : chez
   OpusClip (34 635 vidéos), les débuts « mise en place d'histoire » sont les moins vus.
3. **La 1re image est la plus étrange de la vidéo** (« une 1re image assez intrigante pour aspirer les
   gens », Broken Finger Paradise). Jamais un décor vide, jamais l'horloge seule.
4. **L'image raconte, pas seulement la voix** : à chaque plan il se passe quelque chose de visible
   (une ombre apparaît, une porte s'ouvre, un message arrive, le perso a peur). Un plan = 2 à 3 s max.
5. **Garder le même format, le même perso et le même habillage longtemps** : Fellman a refait 50 vidéos
   du format qui a marché, Zack D. Films publie ≈ 33 vidéos/semaine du même format. On ne change plus de
   concept : seulement les variantes de § 0 bis (format court, ambiance, accroche).
6. **Hashtags : 8 à 10**, mélange niche + général (OpusClip : 10,4 hashtags dans les vidéos virales
   contre 4,8 dans les moins vues ; niche + général = 527 k vues médianes contre 210 k pour niche seul).
   Toujours `#fyp #pourtoi #foryou` + 2-3 généraux (`#horreur #peur #histoire`) + 3-4 précis au sujet
   (`#sms #babysitting #hopital`…). Varier les précis d'une vidéo à l'autre.
7. **Légende courte** : quelques mots + 1 emoji, puis les hashtags (Zack D. Films).

## 0 quinquies. Skills installés dans `.claude/skills/` (choix de Fio, 22/11)

Fio a demandé d'ajouter des skills pour les vidéos. Ils sont dans le dépôt pour que la routine
les ait. **Ils aident, ils ne remplacent rien** : ROUTINE.md gagne toujours en cas de conflit
(formats, durées, voix, style `nuit`, Zernio). `brand-profile.md` (racine) sert de profil ET de
voix pour tous ces skills : ne pas lancer d'interview `brand-profile` / `voice-builder`.

| Quand | Skill à lire |
|---|---|
| Écrire le `texte_accroche` et la 1re phrase (§ 5 étape 3) | `hook-writer` |
| Écrire le script d'une vidéo | `tiktok-script`, `short-form-video-script`, `storytelling-and-narrative`, `story-writer` |
| Mise en scène horreur (3 premières s, plans ≤ 3 s, menace visible, son) | `horreur-baton` |
| Légende + hashtags (§ 0 quater 6-7) | `caption-writer`, `hashtag-strategy` |
| Lire les stats et comprendre pourquoi une vidéo marche ou pas (§ 5 étape 2) | `analytics-and-reporting`, `viral-reverse-engineering`, `experimentation-and-ab-testing`, `tiktok-growth` |
| Contrôle technique avant publication (§ 5 étape 7, EN PLUS de `check_video.py`) | `ffmpeg-skill` : `python3 .claude/skills/ffmpeg-skill/scripts/check.py /tmp/<f>.mp4 --platform tiktok` (0 failed attendu ; les WARN couleur/sous-titres sont normaux) ; specs : `platform-specs-and-validation` |

Les commandes `ffmpeg` déjà écrites dans ce fichier (planche, découpe pour Whisper) restent valables.
Sources (licence MIT) : github.com/social-media-skills/skills, github.com/kajisho5/ffmpeg-skill,
github.com/kaomei/stickman-video-director (seulement les règles d'horreur B4, pas leur moteur
qui demande des services payants).

## 0 ter. Objectif de Fio : PLUS DE 1 000 VUES par vidéo (21/11)

> Fio, 21/11 : « Je veux que ça fasse obligatoirement plus de 1k de vues. » Rien ne peut le garantir
> (pas de faux vues, rien de payant), mais c'est LA priorité de tout le reste.

Ce que disent les chiffres : du 29/10 au 08/11 TOUTES les vidéos faisaient 750-930 vues (quel que soit
le format), depuis le 09/11 toutes font ≈ 230-330. TikTok montre chaque vidéo à un premier lot de
gens ; il ne pousse plus loin QUE si ce lot regarde longtemps, revoit, partage. Les 2 seules vidéos
au-dessus de 1 000 (29/10 : 2 156 et 1 049 vues) avaient 20-23 s de temps moyen et 11-20 %
de vidéos vues jusqu'au bout. Aujourd'hui : 4-9 s et 1-7 %. **Le levier = la rétention.**

Règles obligatoires pour CHAQUE vidéo `nuit` :
1. **`"texte_accroche"`** en tête du JSON (≤ 60 caractères, 1 emoji au plus) : écrit en blanc en haut
   de l'écran les 3 premières secondes (`engine/nuit.js`). Une promesse ou un mystère qu'on ne
   comprend qu'à la fin (« Ma mère est au travail… alors qui toque ? 😨 »). Jamais le titre de la
   série, jamais « Partie 2 ». Différent de la 1re phrase lue.
2. **La 1re phrase lue commence à 0 s** et pose le problème en ≤ 10 mots. Le 1er plan est le plus fort
   de la vidéo (téléphone, ombre, porte qui toque), jamais un décor vide.
3. **Plus court** : `serie` 30-40 s (≤ 680 caractères lus), `histoire` ≤ 32 s, `pov` ≤ 18 s.
   Une vidéo courte vue en entier pousse plus qu'une longue quittée au milieu.
4. **Boucle** : la dernière image ou la dernière phrase renvoie à la première (on revoit la vidéo
   sans s'en rendre compte → « revues » comptées par TikTok). Obligatoire pour `pov` et `histoire`.
5. **Chute promise, chute tenue** : ce que promet le `texte_accroche` arrive au dernier plan, pas avant.
6. **Commentaire facile** : la fin demande une réponse d'1 mot ou d'1 chiffre.
7. **Ne pas se faire bloquer** (3 vidéos à 5-12 vues) : le même jour, jamais 2 vidéos avec le même
   1er plan (même type d'écran ou même décor), la même légende ou les mêmes hashtags ; légende = une
   phrase NEUVE, jamais un modèle rempli.
8. Le plan du jour (`engine/plan.py`) note maintenant d'abord les vues (30 %) et la rétention (30 %),
   et affiche combien de vidéos ont passé 1 000 vues sur 7 jours : le dire à Fio chaque matin,
   honnêtement, même si c'est 0.

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

- **Depuis le 22/11 : les créneaux sont remplis selon `series/plans/<jour>.json` (§ 0 bis).**
  Ce qui suit vaut pour le format `serie` (2 séries au plus en même temps).
- *(Ancien : 4 séries en parallèle, 1 épisode de chacune par jour)*, TikTok +
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
2 bis. **Plan du jour** : `python3 engine/plan.py AAAA-MM-JJ` (§ 0 bis), puis l'appliquer
   (séries arrêtées retirées de `parallel_series`, nouvelles séries ajoutées).
3. **Écrire les vidéos du plan** (`episodes/<prefix>-NN.json`, `"style": "nuit"`, § 1 bis ;
   autres formats : `episodes/<format>-NNN.json` à partir de `episodes/modeles/`), avec
   `format`/`ambiance`/`accroche`, en commençant par celle de 10:00. Nouvelle série : écrire d'abord
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
   - `python3 engine/check_video.py /tmp/<f>.mp4 --min A --max B` doit
     dire OK (A/B = `duree` du créneau dans le plan, ± 3 s ; série : 30 / 50).
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
    ajouter les vidéos à `published` avec `zernio_id`, `format`, `ambiance`, `accroche`),
    `series/plans/<jour>.json`, `series/insights.md`
    et les nouveaux décors de `engine/nuit.js`.
11. **Résumé court en français pour Fio** : les 4 titres, les horaires, les
    réseaux, les votes de la veille, ce que les stats disent (vues, temps
    moyen, complétion) et ce qui change.
