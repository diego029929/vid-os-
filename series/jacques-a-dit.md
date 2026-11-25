# Série « JACQUES A DIT »

**Films source (niche, 07/11)** : Pontypool (2008 : des mots, diffusés à la
radio, contaminent ceux qui les entendent) et Ils (2006 : maison isolée,
assaillants qu'on ne voit presque jamais). On garde : les ordres qui
tombent d'un haut-parleur et qu'on ne peut pas ignorer, l'ennemi presque
invisible, la nuit à tenir. On change : Bretagne, jeu d'enfants, « Jacques »
jamais montré en entier.

Univers : un village de Bretagne près de Saint-Malo. Chaque nuit à minuit,
les haut-parleurs de l'église (et tous les téléphones du village) lancent
une partie de « Jacques a dit ». Règle du jeu, connue de tous les enfants :
- un ordre qui commence par « JACQUES A DIT » : il faut obéir ;
- un ordre SANS « Jacques a dit » : il ne faut PAS le faire (jamais écrire
  « ne bouge pas » : ça contredit les scènes où il faut continuer de courir).
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
lampadaire ; `size`), `jad_station` (intérieur de la station-service ; `hand` main sur la vitre, `sweat` sweat bleu de Léa par terre), `jad_maison` (maison de la grand-mère vue de la ruelle ; `open`, `attic` lueur au grenier), `jad_port` (port de pêche, phare ; `leaving` bateau qui part sans lumière, `phare`, `jacques`), `jad_cabine` (cabine téléphonique du port ; `ring`, `hanging` combiné qui pend, `person` couleur), `jad_ombres` (village des disparus, ciel rouge, ombres ; `n`, `porte`, `jacques`), `jad_porte` (église des disparus, porte de lumière ; `shadow`). Tous acceptent `aube` (ciel d'aube, épisode 6),
`dark`, `red`, `figure`. Compléter avec les décors génériques (`chambre`,
`porte`, `escalier`, `foret`, `station`, `eglise`, `cimetiere`, `plage`…). L'horloge avance de minuit (ép. 1) à l'aube (ép. 6).

| Ép. | Ordre / règle | Situation / choix | Suspense final |
|---|---|---|---|
| 1 | « Jacques a dit : éteins la lumière », puis « allume » sans Jacques | A rallumer / B ne pas bouger | « Jacques a dit : ouvre ta porte. » Quelqu'un est derrière. A ouvrir / B ne pas ouvrir |
| 2 | On doit obéir : la porte s'ouvre sur Léa. « Jacques a dit : cours jusqu'à la station-service », puis « arrête-toi » sans Jacques | A t'arrêter / B continuer | « Jacques a dit : ferme les yeux jusqu'à l'aube. » Léa crie qu'il est derrière toi. A fermer / B garder ouverts |
| 3 | Écrit le 08/11 (ep24). Réponse : fermer les yeux (Léa les garde ouverts et disparaît). La « grand-mère » appelle sans « Jacques a dit » | A courir chez elle / B rester dans la station (bonne : B ; c'était un faux, « mon chéri ») | À l'église, la vraie grand-mère. « Jacques a dit : laisse-la ici et retourne à la station. » A la laisser / B l'emmener |
| 4 | Écrit le 09/11 (ep25, forme « Line 9 »). Vote partie 3 : la laisser (1 voix + tirage). Règle 3 découverte : les téléphones imitent Jacques, seuls les haut-parleurs de l'église disent vrai (pêcheur et voisin disparaissent ; compteur DISPARUS 1→3) | ligne droite, pas de choix au milieu | « Jacques a dit : choisis qui je prends avant l'aube. » A ma grand-mère (tu vis) / B moi (tu rejoins les disparus, là où est Léa) : le vote décide la partie 5 |
| 5 | Écrit le 09/11 (ep26). Vote partie 4 : 1 A / 1 B → tirage = « moi ». Le héros se réveille dans le village des disparus (ciel rouge, ombres). Règle 3 d'ici : ne jamais dire son prénom (sinon on devient une ombre). Théo (10 ans, petit frère de Léa) la dit et devient une ombre | ligne droite | « Jacques a dit : à l'aube, tu rentres, et tu ramènes une seule personne, même une ombre. » A Léa (vivante) / B Théo (l'ombre ; Léa supplie) |
| 6 | Écrit le 10/11 (ep27). Vote partie 5 : 0 vote → tirage = Léa. Sortie par le couloir de l'église (règle 3 « Jacques a dit : ne vous retournez jamais »), la voix de Théo appelle derrière (compteur VOIX DERRIÈRE TOI 0→3). Aube à Saint-Malo, les mêmes haut-parleurs : « joue toute la nuit pour une ombre et elle reviendra » (sans « Jacques a dit » : piège ?) | ligne droite | A jouer avec Léa ce soir pour Théo / B rester avec ta grand-mère (le vote décide « la suite ») |

Les épisodes publiés sont listés dans `series/state.json`.
