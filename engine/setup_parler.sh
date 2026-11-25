#!/bin/sh
# Installe Parler-TTS (voix « 2 » choisie par Fio le 04/11) dans un environnement
# Python séparé, pour ne pas changer la version de transformers utilisée ailleurs.
set -e
V=${PARLER_VENV:-/tmp/parler-venv}
[ -x "$V/bin/python" ] || python3 -m venv --system-site-packages "$V"
"$V/bin/pip" install -q parler-tts
echo "parler prêt : $V/bin/python"
