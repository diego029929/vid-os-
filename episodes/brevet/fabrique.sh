#!/usr/bin/env bash
# Fabrique une vidéo « brevet » (style stick-figure) : son -> images -> MP4.
#   bash episodes/brevet/fabrique.sh episodes/brevet/<dossier> [sortie.mp4]
# Avant : python3 episodes/brevet/voix.py <dossier>  (voix + web/words.js)
# Images seules pour vérifier : (cd <dossier> && node <render.js> stills 1.5,6,12)
set -euo pipefail
ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RENDER="$ICI/../../.claude/skills/stick-figure/engine/tools/render.js"
DIR="$(cd "${1:?usage: fabrique.sh <dossier> [sortie.mp4]}" && pwd)"
OUT="${2:-$DIR/$(basename "$DIR").mp4}"
WORKERS="${WORKERS:-4}"
cd "$DIR"
[ -f web/words.js ] || { echo "lancer d'abord voix.py"; exit 1; }
echo "== son"; python3 audio.py
echo "== images ($WORKERS en parallèle)"
rm -rf seg; mkdir -p seg
N=$(grep -c "^shot(" web/shots.js)
pids=()
for ((w = 0; w < WORKERS; w++)); do
  ids=""; for ((i = w; i < N; i += WORKERS)); do ids="${ids:+$ids,}$i"; done
  [ -n "$ids" ] && { node "$RENDER" segments "$ids" > "seg/log$w.txt" 2>&1 & pids+=($!); }
done
for p in "${pids[@]}"; do wait "$p"; done
grep -h "\[err\]" seg/log*.txt && { echo "erreur JavaScript, voir seg/log*.txt"; exit 1; } || true
[ "$(ls seg/shot_??.mp4 | wc -l)" -eq "$N" ] || { echo "un plan a raté, voir seg/log*.txt"; exit 1; }
for f in seg/shot_??.mp4; do echo "file '$PWD/$f'"; done > seg/list.txt
ffmpeg -v error -y -f concat -safe 0 -i seg/list.txt -c copy seg/muet.mp4
echo "== assemblage"
ffmpeg -v error -y -i seg/muet.mp4 -i audio/mix.wav -map 0:v -map 1:a -c:v copy \
  -af "alimiter=limit=0.8:attack=2:release=60,loudnorm=I=-14:TP=-1.5:LRA=9" \
  -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "$OUT"
echo "ok : $OUT"
