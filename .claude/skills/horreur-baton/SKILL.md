---
name: horreur-baton
description: Règles de mise en scène pour les courtes vidéos d'horreur dessinées (accroche des 3 premières secondes, plans de 3 s max, menace visible, son). À lire avant d'écrire ou de vérifier un épisode d'horreur fait avec engine/nuit.py.
---

# Horreur bâton : règles de mise en scène

Repris du style « B4 · Survival Thriller » de Stickman Video Director
(github.com/kaomei/stickman-video-director, licence MIT, voir `LICENSE`).
On n'installe PAS leur moteur (il demande des générateurs d'images et de voix
payants et pèse 500 Mo) : on applique seulement leurs règles de mise en scène
avec NOTRE moteur (`engine/nuit.py`, voix Piper, ROUTINE.md). En cas de
conflit, ROUTINE.md gagne.

Les fichiers complets (en anglais) sont dans `references/`. Certains liens
qu'ils contiennent pointent vers des fichiers du dépôt d'origine qui ne sont
pas copiés ici : les ignorer.

## Les règles à appliquer à chaque épisode

1. **Les 3 premières secondes progressent.** Pas juste un titre posé sur une
   image fixe : une phrase d'accroche courte en deux temps (mise en place,
   puis la chute affichée d'un bloc, jamais mot par mot), ET un changement
   visible dans l'image (le personnage passe de l'inquiétude à la peur, un
   objet change d'état, une trace de la menace apparaît). Voir
   `references/b4-opening-direction.md`.
2. **Aucun plan ne reste plus de 3 secondes sans changement réel** de l'image
   principale. Un sous-titre qui change, un petit zoom ou du grain ne comptent
   pas. Voir `references/b4-picture-animation.md`.
3. **La menace doit se voir à la taille d'un téléphone**, sans le son ni le
   texte : silhouette, échelle, ce qui est caché ou bloqué, contraste. Plus de
   noir ou de sang n'est pas mieux. Ne pas montrer la fin trop tôt. Voir
   `references/b4-survival-storytelling.md`.
4. **Le texte a un rôle dramatique** : la question d'accroche n'est pas un
   simple sous-titre ; elle reste à l'écran assez longtemps pour être lue.
   Voir `references/b4-typography-acceptance.md`.
5. **Le son suit l'histoire** : une ambiance par scène, des bruits liés à ce
   qu'on voit, des silences voulus. Pas de jump scare automatique. Voir
   `references/b4-audio-direction.md`.
6. **Vérifier la vraie vidéo** (planche contact + écoute), pas seulement le
   JSON : une vidéo qui s'encode sans erreur n'est pas forcément bonne. Voir
   `references/b4-repeatability-check.md`.
