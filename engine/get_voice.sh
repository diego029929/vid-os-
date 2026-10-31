#!/bin/sh
# Télécharge les voix françaises Piper (gratuites) dans assets/voices/.
# Usage : ./engine/get_voice.sh [nom_de_voix ...]  (par défaut : celle de engine/voice_config.json)
# Nécessite que huggingface.co soit autorisé dans le réseau de l'environnement.
set -e
cd "$(dirname "$0")/.."
mkdir -p assets/voices
voices="$*"
[ -n "$voices" ] || voices=$(python3 -c "import json; print(json.load(open('engine/voice_config.json'))['voice'])")
for v in $voices; do
  # fr_FR-tom-medium -> fr/fr_FR/tom/medium
  speaker=$(echo "$v" | cut -d- -f2)
  quality=$(echo "$v" | cut -d- -f3)
  base=https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/$speaker/$quality
  for f in "$v.onnx" "$v.onnx.json"; do
    [ -s "assets/voices/$f" ] || curl -sSfL -o "assets/voices/$f" "$base/$f"
  done
done
echo "voix prête : $voices"
