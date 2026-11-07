# Série « JACQUES A DIT »

**Films source** : Squid Game (jeu d'enfants mortel, règles simples) et
Le Village / Sans un bruit (un village entier qui obéit à une règle la nuit).
On garde : la règle de jeu, l'ordre qui tombe d'un haut-parleur, le village
vide. On change : Bretagne, héros seul, « Jacques » jamais montré en entier.

Univers : un village de Bretagne près de Saint-Malo. Chaque nuit à minuit,
les haut-parleurs de l'église (et tous les téléphones du village) lancent
une partie de « Jacques a dit ». Règle du jeu, connue de tous les enfants :
- un ordre qui commence par « JACQUES A DIT » : il faut obéir ;
- un ordre SANS « Jacques a dit » : il ne faut PAS bouger.
Celui qui se trompe disparaît avant l'aube. Héros : personnage bâton, sweat
orange, rentré voir sa grand-mère. Personnages : Léa, la voisine (sweat
bleu, a déjà perdu son frère au jeu), « Jacques » (on ne le voit jamais :
une silhouette sans visage, costume noir). But : tenir jusqu'à l'aube.

Genre reconnaissable en 1 seconde (jeu d'enfants qui tourne mal, ordres
au haut-parleur, village vide la nuit), histoire originale.

Ton : angoissant, phrases très courtes, tutoiement, jamais gore.

**Décors PROPRES À LA SÉRIE (07/11, demande de Fio) : les utiliser en
priorité, au moins 3 par épisode** : `jad_place` (place du village, église
aux haut-parleurs ; `jacques` true pour le montrer, `jacques_at` [u, v],
`jacques_size`), `jad_clocher` (horloge + pavillons ; `hour` 0-6 pour
l'heure), `jad_mamie` (salle de la grand-mère, armoire bretonne ; `ring`
le téléphone sonne, `mamie` silhouette, `eyes`), `jad_ruelle` (ruelle de
granit, téléphone par terre ; `jacques`), `jad_remparts` (remparts de
Saint-Malo et la mer ; `jacques`), `jad_jacques` (Jacques sous le
lampadaire ; `size`). Tous acceptent `aube` (ciel d'aube, épisode 6),
`dark`, `red`, `figure`. Compléter avec les décors génériques (`chambre`,
`porte`, `escalier`, `foret`, `station`, `eglise`, `cimetiere`, `plage`…). L'horloge avance de minuit (ép. 1) à l'aube (ép. 6).

| Ép. | Ordre / règle | Situation / choix | Suspense final |
|---|---|---|---|
| 1 | « Jacques a dit : éteins la lumière », puis « allume » sans Jacques | A rallumer / B ne pas bouger | « Jacques a dit : ouvre ta porte. » Quelqu'un est derrière. A ouvrir / B ne pas ouvrir |
| 2 | On doit obéir : la porte s'ouvre sur Léa. « Jacques a dit : cours jusqu'à la station-service », puis « arrête-toi » sans Jacques | A t'arrêter / B continuer | « Jacques a dit : ferme les yeux jusqu'à l'aube. » Léa crie qu'il est derrière toi. A fermer / B garder ouverts |
| 3 | Un ordre glissé dans la voix de ta grand-mère | à écrire | à écrire |
| 4 | Deux ordres en même temps (haut-parleur et téléphone) | à écrire | à écrire |
| 5 | « Jacques » est dans le village | à écrire | à écrire |
| 6 | L'aube : le dernier ordre | à écrire | dilemme final |

Les épisodes publiés sont listés dans `series/state.json`.
