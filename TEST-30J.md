# Test 30 jours : horreur vs explications scolaires

> Décidé avec Fio le 25/11/2026. But : arrêter de chercher « la niche pas saturée » et
> laisser les chiffres choisir.
>
> **Changement du 25/11 au soir (Fio) : l'horreur s'arrête.** Le compte @4_youchoose_4 est vidé et
> devient la chaîne scolaire (pas de 2e compte). La piste A ne publie plus : ses chiffres des
> 10 dernières vidéos servent de **point de référence**, et le scolaire doit faire mieux.
> Ce fichier ne change rien à ROUTINE.md tant que Fio n'a pas validé l'épisode pilote (étape 0).

## Les deux pistes

| | A · Horreur (ARRÊTÉE le 25/11, sert de référence) | B · Explications scolaires (nouveau) |
|---|---|---|
| Compte | @4_youchoose_4 (TikTok + Insta) | **le même compte**, vidé, renommé, bio changée |
| Style | « Nuit & téléphone » (`engine/nuit.py`) | stick-figure (skill `stick-figure`), monde cartoon coloré |
| Voix | Pocket TTS `estelle` | la même (`voix-pocket-tts`), jamais Kokoro ni ElevenLabs |
| Rythme | 3/jour jusqu'au 25/11 | **1/jour à 18h** (après les cours), 30 vidéos |
| Durée | 25-40 s | 35-45 s |
| Public | 16-25 ans, le soir | collégiens de 3e (14-15 ans), révisions du brevet |

**Point de départ A (7 derniers jours, `series/insights.md`)** : ≈ 200 vues par vidéo, temps moyen 4-13 s,
0 vidéo sur 36 au-dessus de 1 000 vues.

## Règle de décision (fixée AVANT de publier, on ne la change pas en route)

Le 25/12, on compare les **10 dernières vidéos scolaires** aux **10 dernières vidéos d'horreur** (du 22 au 25/11,
chiffres dans `series/insights.md`). Les premières vidéos scolaires servent à « réapprendre » le compte à TikTok.

1. **Rétention** = temps moyen ÷ durée. C'est le critère n°1 (c'est ce qui fait pousser TikTok).
2. **Abonnés gagnés pour 1 000 vues.**
3. **Vues médianes** (la médiane, pas la moyenne : une vidéo chanceuse ne doit pas tout fausser).

- B gagne si elle bat A sur **au moins 2 critères sur 3** → on continue le scolaire (passage à 2/jour, puis le programme de 4e).
- A gagne sur au moins 2 critères sur 3 → le scolaire ne marche pas mieux : on en reparle avec Fio (reprendre l'horreur, autre angle).
- Si l'écart est < 20 % partout → égalité : on garde celle qui demande le moins de travail par vidéo.

**Arrêt anticipé** : si au jour 15, B fait moins de 50 vues de médiane sur 7 vidéos d'affilée, on refait 3 vidéos
avec un autre angle d'accroche ; si ça ne bouge toujours pas, on arrête B.

## Étape 0 — Épisode pilote (rien n'est publié avant que Fio dise oui)

1. Script du pilote (sujet 1 ci-dessous), montré à Fio **avant** l'animation.
2. Vérification de chaque fait avec 2 sources (manuel / Lumni / site d'un musée ou d'une université).
3. Rendu stick-figure avec la voix estelle (calage des mots par Whisper, pas Parakeet qui est anglais).
4. Fio regarde le MP4. Oui → on lance. Non → on corrige le style, pas le sujet.

## Format d'une vidéo B (« Le brevet en 40 secondes »)

1. **0-2 s : accroche = une question ou un fait qui surprend**, liée au chapitre
   (« En 1914, l'Europe entre en guerre… à cause d'un sandwich ? » → puis on corrige l'idée reçue).
2. **2-30 s : 3 idées maximum**, une par plan, celles qui tombent au brevet (dates, notions, acteurs).
3. **30-38 s : « Ce qu'il faut retenir »** = 1 phrase + 1 date, écrite à l'écran.
4. **Fin : question pour commenter** (« Tu savais ? Oui ou non ») et la dernière image renvoie à la première (boucle).
5. Titre = le nom du chapitre tel que les élèves le tapent : « Brevet histoire : la guerre froide en 40 secondes ».
6. Jamais de fait non vérifié. Jamais de blague sur les victimes (génocides, guerres) : ton sérieux sur ces sujets.

## Les 20 premiers sujets (programme officiel d'histoire-géo de 3e)

Ordre = ordre du programme, pour que les élèves suivent la série du début à la fin.

| # | Chapitre | Accroche de départ |
|---|---|---|
| 1 | Première Guerre mondiale : une guerre totale | « Pourquoi on l'appelle "totale" ? » |
| 2 | La vie dans les tranchées (Verdun) | « 300 jours, 300 000 morts, pour quelques kilomètres » |
| 3 | La révolution russe et l'URSS de Staline | « Un pays où ta photo pouvait disparaître des livres » |
| 4 | L'Allemagne nazie : comment Hitler arrive au pouvoir | « Il n'a pas pris le pouvoir par la force » |
| 5 | Totalitarisme : la définition en 3 points | « 3 signes qu'un pays est totalitaire » |
| 6 | Seconde Guerre mondiale : guerre d'anéantissement | « Pourquoi elle est différente de la première » |
| 7 | Le génocide des Juifs et des Tsiganes | ton sérieux, sans accroche choc |
| 8 | La France de Vichy et la collaboration | « La France a eu deux gouvernements en même temps » |
| 9 | La Résistance (Jean Moulin, le CNR) | « Comment résister quand tout est interdit ? » |
| 10 | 1944-1947 : refonder la République (vote des femmes, Sécu) | « Pourquoi tu as la Sécu ? Tout part de 1945 » |
| 11 | La guerre froide en 40 secondes | « Une guerre où les deux géants ne se tirent jamais dessus » |
| 12 | Le mur de Berlin et la crise de Cuba | « 13 jours où le monde a failli finir » |
| 13 | La décolonisation (Inde, Algérie) | « Comment un pays devient indépendant ? » |
| 14 | La construction européenne | « Pourquoi des ennemis ont fait un club ensemble » |
| 15 | Le monde après 1989 | « Le mur tombe… et ensuite ? » |
| 16 | La Ve République et de Gaulle | « Pourquoi on dit "la Cinquième" ? » |
| 17 | Alternance et cohabitation | « Un président et un Premier ministre ennemis » |
| 18 | Femmes et hommes 1950-1980 (droits des femmes) | « En 1965, ta mère n'aurait pas pu ouvrir un compte » |
| 19 | Géo : les aires urbaines en France | « 8 Français sur 10 vivent en ville… vraiment ? » |
| 20 | Géo : la France et l'Union européenne | « Ce que l'Europe change dans ta vie, demain matin » |

(Chaque chiffre des accroches est revérifié à l'étape « faits » avant d'écrire le script.)

## Chaque jour (piste B, en plus de la routine A)

1. Script (skills `short-form-video-script`, `hook-writer`) + vérification des faits.
2. Test du spectateur : un agent neuf joue un élève de 3e qui n'a rien vu → compris ? clarté ≥ 8/10.
3. Rendu stick-figure, planche contact, transcription Whisper, `check_video.py` + `check.py --platform tiktok`.
4. Programmation Zernio à 18h sur le compte B ; noter dans `series/test-30j.json`
   (date, sujet, vues, temps moyen, complétion, abonnés gagnés).
5. Le 25/12 : appliquer la règle de décision, tableau final dans ce fichier.

## Décisions de Fio (à remplir)

- [x] Compte : le même (@4_youchoose_4), vidé de l'horreur (Fio, 25/11).
- [ ] Les 78 vidéos supprimées par Fio dans les applis TikTok et Instagram (Zernio ne peut pas : voir plus bas).
- [ ] Nouveau nom, photo et bio du compte.
- [ ] Pilote validé ?

## Pourquoi les vidéos se suppriment à la main

Doc Zernio (docs.zernio.com, lu le 25/11) : `DELETE /v1/posts/{id}` refuse les posts publiés, et
`POST /v1/posts/{id}/unpublish` « n'est pas pris en charge sur Instagram ni TikTok ». Aucune API ne retire
une vidéo déjà en ligne sur ces deux réseaux : il faut le faire dans les applis. Ne PAS supprimer les posts
dans Zernio : ça effacerait aussi leurs statistiques, qui servent de référence au test.
