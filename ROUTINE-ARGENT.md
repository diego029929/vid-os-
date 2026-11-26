# Routine quotidienne ASTUCES ARGENT (depuis le 27/11/2026)

> Décisions de Fio, 26/11 au soir :
> - nouvelle niche : **astuces argent et économies du quotidien** (vidéos sans visage, en français) ;
> - **publier sur le TikTok déjà connecté** dans Zernio (@4_youchoose_4, `accountId` `6aef19cf4f6bb8199749fd84`),
>   **TikTok seulement** (pas d'Instagram) ;
> - **publier directement**, sans attendre de validation ;
> - **3 vidéos par jour à 10:00, 18:00 et 20:00 (Europe/Paris)** ;
> - « attention au choix de la voix, c'est presque le plus important, fais une voix naturelle ».
>
> La routine horreur (`ROUTINE.md`) est en pause depuis le 25/11 : ne pas la relancer, ne pas publier d'horreur.
> Ce fichier prime sur `ROUTINE.md` et `brand-profile.md` pour tout ce qui touche aux vidéos argent.
> On réutilise le moteur (`engine/nuit.py`), les contrôles et Zernio décrits dans `ROUTINE.md` § 4-5.
> Tout le travail argent se fait sur la branche **`argent`** (commit + push sur `argent`, jamais sur main).

## 1. La voix (le plus important)

- Moteur : **Chatterbox multilingue** (`chatterbox-tts`, gratuit, local), langue `fr`, qui copie le timbre de
  `assets/ref/ref-narrateur-grave.wav` (voix d'homme LibriVox, domaine public, déjà choisie par Fio le 09/11).
  Ton posé et chaleureux, comme un ami qui donne un bon plan. Pas d'effet radio/mégaphone.
- Variables à exporter AVANT chaque rendu (elles écrasent `engine/voice_config.json`, qui reste celui de l'horreur) :
  ```bash
  export VOICE=chatterbox VOICE_REF=ref-narrateur-grave.wav VOICE_EXAG=0.5 VOICE_CFG=0.5 VOICE_FX=aucun VOICE_TEMPO=1.05
  ```
- **Jamais** Pocket `estelle` (Fio : « nulle »), jamais Piper, jamais une voix payante ou clonée d'un vrai créateur.
- Le 1er jour (fichier `argent/voix-ok.txt` absent) : générer la phrase « Tu paies sûrement un abonnement que tu
  n'utilises plus. Ouvre ton appli bancaire. » avec ces réglages puis avec `VOICE_EXAG=0.35` et `0.7`,
  retranscrire chacune avec Whisper medium, garder la plus claire ET la moins monotone (écouter le débit : pas de
  mot avalé, pas de pause bizarre), écrire le réglage gardé et pourquoi dans `argent/voix-ok.txt`, puis l'utiliser.
  Si Chatterbox ne s'installe pas ou bégaie sur 3 phrases d'affilée : passer à Pocket `cosette`
  (`VOICE=pocket`, `pocket_voice` via `voice_config`… ou `pocket-tts --voice cosette`), le dire dans le résumé.
- Chaque phrase est vérifiée avec Whisper (règles de `ROUTINE.md` § 4) : mot répété, bégayé ou mal lu = relancer
  (jusqu'à 3 fois), puis changer la tournure. Écrire les nombres en lettres dans `voice` (« neuf euros
  quatre-vingt-dix-neuf »), les sigles en clair. Ne jamais publier une voix défectueuse.

## 2. Le format « astuce » (25-35 s)

Modèle : `episodes/argent/argent-001.json`. Champs : `"style": "nuit"`, **`"theme": "argent"`** (cartes vertes,
étiquette dorée « ASTUCE N° »), `"format": "astuce"`, `"ambiance": "jour"` (décors éclaircis), `"accroche"`.
1. **1re seconde = un détail concret qui touche le portefeuille**, montré à l'écran : notification de banque,
   ticket de caisse, relevé, étiquette de prix (`tel` : `notif`, `sms` comme liste). Jamais un décor vide.
2. 1re phrase lue ≤ 10 mots, commence à 0 s, tutoiement.
3. 1 à 3 cartes `regle` (= « ASTUCE N° ») avec ≤ 6 mots chacune ; entre elles, un plan qui montre l'astuce.
4. Fin : question à réponse d'1 mot ou d'1 chiffre (« Combien t'en as trouvé ? Écris le chiffre »). Si possible,
   la dernière image rappelle la première (boucle).
5. Légende courte + 1 emoji + 8-10 hashtags : `#fyp #pourtoi #foryou` + 2-3 parmi `#argent #economies #astuce
   #budget #epargne #bonplan` + 2-3 précis au sujet. Jamais deux fois la même légende ni le même 1er plan le même jour.
6. `"video_made_with_ai": true` dans Zernio (voix de synthèse).

## 3. Règles de contenu (obligatoires)

- **Que du vrai, vérifiable, valable en France.** Tout chiffre, loi ou date : vérifier sur une source officielle
  ou sérieuse (service-public.fr, economie.gouv.fr, ADEME, INC, 60 Millions de consommateurs) et noter la source
  dans `argent/sujets.md`. Dans le doute, enlever le chiffre.
- **Jamais** : conseil d'investissement, crypto, bourse, paris, crédit, « deviens riche », promesse de gain,
  marque citée en mal, faux témoignage, lien de parrainage (tant que Fio ne l'a pas demandé).
- Sujets : économies du quotidien (courses, énergie, abonnements, téléphone, transport, banque, aides officielles
  méconnues, pièges marketing, budget simple). Banque d'idées et sujets déjà faits : `argent/sujets.md`
  (cocher ce qui est publié, en ajouter 5 nouvelles chaque lundi).

## 4. Chaque matin (tâche planifiée)

0. Installer comme `ROUTINE.md` § 5 étape 0 (torch CPU, `chatterbox-tts`, `openai-whisper`, `playwright`,
   `num2words`). `git fetch origin argent && git checkout argent`.
1. Zernio `GET /v1/accounts` : si le TikTok a `needsReconnection` ou si un post d'hier est `failed`, le dire en premier.
2. Stats des vidéos argent (`GET /v1/analytics`, posts dont le `zernio_id` est dans `argent/state.json`) : vues,
   likes, commentaires, partages, temps moyen, complétion. Une section par jour dans `argent/insights.md`.
   À partir de 6 vidéos notées : refaire plus souvent les types de sujets / accroches du tiers du haut
   (temps moyen et abonnés d'abord), moins souvent ceux du tiers du bas. Le dire dans le résumé avec le chiffre.
3. Écrire les 3 vidéos du jour (`episodes/argent/argent-NNN.json`), 3 sujets de familles différentes.
4. Relecture `python3 engine/check_script.py <f>` + test du spectateur (`ROUTINE.md` § 5 étape 4 : « clarté » et
   « j'ai appris un truc utile » ≥ 8/10, sinon corriger).
5. Rendu UN À LA FOIS (brouillon + planche, puis rendu complet) dans l'ordre 10h, 18h, 20h.
6. Contrôles `ROUTINE.md` § 5 étape 7 (planche regardée, Whisper, `check_video.py --min 22 --max 38`, -14 LUFS).
7. Branche `media` (§ 5 étape 8, worktree, sans push forcé), puis **programmer dans Zernio** comme § 5 étape 9
   mais `platforms` = TikTok seul, `scheduledFor` à 10:00 / 18:00 / 20:00 Paris (UTC = Paris − 1 h en hiver,
   − 2 h en été) ; heure passée → `publishNow`. Vérifier `GET /v1/posts/{id}`.
8. Noter dans `argent/state.json` → `published` : fichier, sujet, accroche, créneau, `zernio_id`. Commit + push
   sur `argent`.
9. Résumé court en français pour Fio : les 3 titres et horaires, les stats d'hier (honnêtement, même faibles),
   ce qui change aujourd'hui. Pas de jargon.
