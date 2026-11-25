# Exemple 3D : « Une balle VS une armure de chevalier » (22/11, ≈ 14 s, test)

Fait avec le skill `zach-d-films` (three.js) + `voix-pocket-tts` + `sound-effects`. Résultat livré à Fio :
`/mnt/project-files/essais-22-11/balle-vs-armure-3d-v2.mp4`.

Ici les plans 3D sont ceux de l'exemple du skill (armure), resserrés avec une « déformation du temps »
(`WARP`). Pour une NOUVELLE histoire, il faut écrire de nouveaux plans dans `src/shots.js`
(un plan toutes les 2-3 s, cf. `.claude/skills/zach-d-films/SKILL.md`), et `WARP` devient inutile
(mettre `[[0, DURATION, 0, DURATION]]`).

## Refaire / adapter (depuis la racine du dépôt)
```bash
pip install -q pocket-tts faster-whisper soundfile
(cd .claude/kit && npm install --no-audit --no-fund)          # PAS `playwright install`
cp -R episodes/3d/balle-vs-armure episodes/3d/<sujet> && cd episodes/3d/<sujet>
ln -s ../../../.claude/kit/node_modules node_modules && mkdir -p audio
# 1. script.json = liste de phrases (Zack D. Films : question, idée reçue, « Mais/Faux », exemples, chute)
python3 voix.py .                      # 1 wav par phrase (voix du dépôt : Pocket TTS estelle)
# 2. Vérifier CHAQUE phrase avec faster-whisper (word_timestamps=True, audio passé en numpy 16 kHz),
#    refaire/changer la tournure si un mot est faux ; noter les débuts des groupes de 1-3 mots.
# 3. build.py : mettre les sous-titres (caps = décalages par phrase), WARP et FADES → écrit src/shots.js
#    (repartir d'un shots.js propre : build.py remplace DURATION/CAPTIONS/FADES)
python3 build.py
GL=swiftshader node render.mjs stills 0.5,3,6,9,12 stills     # REGARDER avant le rendu complet
# 4. Rendu en 3 morceaux parallèles (≈ 5 s/image chacun, ≈ 15-25 min pour 30 s), puis concat
GL=swiftshader node render.mjs video part1.mp4 30 0 10 & GL=swiftshader node render.mjs video part2.mp4 30 10 20 & GL=swiftshader node render.mjs video part3.mp4 30 20 & wait
printf "file part1.mp4\nfile part2.mp4\nfile part3.mp4\n" > l.txt && ffmpeg -f concat -i l.txt -c copy silent.mp4
# 5. Bruitages : mix.py (moments des impacts = temps des plans ; coups de feu et métal synthétisés,
#    whoosh/impacts de la bibliothèque CC0 du skill sound-effects)
python3 mix.py
ffmpeg -i silent.mp4 -i audio/mix.wav -map 0:v -map 1:a -vf scale=1080:1920:flags=lanczos -c:v libx264 -crf 18 \
  -pix_fmt yuv420p -af "apad,loudnorm=I=-14:TP=-2,aresample=44100,alimiter=limit=0.7:level=false" -c:a aac -b:a 192k -shortest final.mp4
python3 ../../../.claude/skills/ffmpeg-skill/scripts/check.py final.mp4 --platform tiktok   # 0 failed
```
Ne PAS commiter `audio/`, `stills/`, les mp4 ni `node_modules`.

Pièges vus :
- `render.mjs` : `executablePath: '/opt/pw-browsers/chromium'` (déjà mis ici) car le kit pinne Playwright 1.49.1.
- Pas de GPU dans le conteneur → `GL=swiftshader`.
- Accroche texte : `#hook` dans `index.html`, visible 3 s (`hookEl` dans `src/main.js`).
- Sans `loudnorm TP=-2` + `alimiter level=false`, le true peak dépasse (check.py FAIL).
