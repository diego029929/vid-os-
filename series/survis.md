# Format court « SURVIS ? » (test à partir du 03/11)

TEST validé par Fio le 02/11 au soir : on GARDE la série du jour (3 épisodes
à 10h, 12h, 18h) et on AJOUTE chaque jour 2 vidéos courtes « SURVIS ? N°X »
à 15:00 et 20:30. Pourquoi : les séries longues font ~800 vues, presque aucun
commentaire, et sur Instagram les gens partent après 5 à 14 s ; un nouveau
spectateur qui tombe sur une « partie 3 » passe. Les anciennes vidéos courtes
du compte faisaient plus de commentaires (39 s : 13 commentaires).
Bilan après 3 jours (le 06/11, une fois les stats remontées) : comparer le
score des courtes et des épisodes dans `series/insights.md` et le dire à Fio
dans le résumé ; c'est Fio qui décide de la suite.

- **vidéos courtes de 30 à 40 s, chacune complète et indépendante** :
  on la comprend sans rien avoir vu d'autre, donc chaque vidéo peut
  devenir virale seule ;
- **numérotées** (« SURVIS ? N°12 ») pour donner envie de regarder les
  autres et de s'abonner ;
- **2 vidéos par jour**, en plus de la série ;
- **un choix A/B au cœur de la vidéo** : le spectateur doit répondre dans
  sa tête en 3 secondes, puis on voit le mauvais choix → « TU ES MORT. » →
  « on rembobine » → le bon choix ;
- **fin = nouvelle question qui fait commenter** (un dilemme où les deux
  réponses se défendent, ou « tu aurais tenu combien de temps ? »), puis
  « ABONNE-TOI POUR LE N° SUIVANT ».

## Structure d'une vidéo (20 à 28 plans, 30-40 s)

1. Accroche (1 plan, < 2 s) : une image choc ou une phrase qui fait peur,
   au cœur de l'action. Jamais la même formule d'une vidéo à l'autre.
2. Situation + règle (4-6 plans) : où on est, le danger, la règle à suivre.
3. Choix A/B avec compte à rebours 3 s (1 plan, `"dur": 3.2`).
4. Mauvais choix joué (3-4 plans, `record`) → « TU ES MORT. » → `rewind`.
5. Bon choix (3-5 plans) + retournement final.
6. Question pour les commentaires (1-2 plans, cartes A/B sans réponse) +
   « ABONNE-TOI POUR LE N° SUIVANT. »

## Banque d'idées (cocher quand utilisée, ne jamais refaire la même)

- [ ] Ascenseur qui s'arrête à un étage qui n'existe pas
- [ ] Quelqu'un frappe à 3 h, avec la voix de ta mère, alors qu'elle dort
- [ ] Ton reflet cligne des yeux en retard
- [x] Appel de ton propre numéro (N°3, 04/11)
- [x] Station-service vide la nuit, une règle sur la porte (N°2, 03/11)
- [ ] Hôtel : la chambre 313 n'a pas de fenêtre
- [x] Forêt : quelqu'un siffle ton prénom (N°5, 05/11)
- [x] Panne de courant : une bougie s'allume toute seule (N°4, 04/11)
- [ ] Message : « ne te retourne pas, je suis derrière toi »
- [ ] Livraison de nuit : le livreur ne bouge plus devant l'immeuble
- [x] Baby-sitting : l'enfant dit qu'il y a un monsieur sous le lit (N°8, 06/11)
- [ ] Tunnel : les phares d'en face s'éteignent
- [ ] Piscine fermée : quelqu'un nage dans le noir
- [ ] Camping : une tente de plus qu'hier
- [ ] Musée la nuit : un tableau a changé
- [ ] Bus de nuit : le chauffeur prend une route qui n'existe pas
- [ ] Neige : des traces de pas qui finissent au milieu du champ
- [ ] Hôpital : l'étage -2 n'est pas sur le plan
- [x] Brouillard : quelqu'un te demande l'heure trois fois (N°7, 06/11)
- [ ] Radio de survie : « si le ciel devient vert, n'ouvre pas »
- [x] Parking souterrain : ta voiture n'est plus à sa place (N°6, 05/11)
- [ ] Jeu vidéo : ton personnage regarde la caméra
- [x] Concierge : « ne réponds jamais à l'interphone après minuit » (N°1, 03/11)

## Fabrication

- Fichiers `episodes/survis-NN.json` (NN = numéro N), même format style 2
  que les épisodes (`episodes/essai-style2.json`), même moteur, même voix,
  même contrôle Whisper (zéro bégaiement), durée vérifiée 30-40 s.
- Numéro suivant : `survis_next` dans `series/state.json`.
- `title` : « SURVIS ? N°X · » + une question qui donne envie de répondre ;
  `subtitle` : « N°X ». Pas de « partie », pas de lien avec la série.
- Rendre les courtes APRÈS les 3 épisodes du jour (un seul rendu à la fois).
