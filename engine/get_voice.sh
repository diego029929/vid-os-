#!/bin/sh
# Télécharge la voix française Piper (gratuite) dans assets/voices/.
# Nécessite que huggingface.co soit autorisé dans le réseau de l'environnement.
set -e
cd "$(dirname "$0")/.."
mkdir -p assets/voices
base=https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium
for f in fr_FR-siwis-medium.onnx fr_FR-siwis-medium.onnx.json; do
  [ -s "assets/voices/$f" ] || curl -sSfL -o "assets/voices/$f" "$base/$f"
done
echo "voix prête"
