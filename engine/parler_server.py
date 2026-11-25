"""Petit serveur Parler-TTS : lit une requête JSON par ligne sur stdin
({"text", "desc", "seed", "out"}), écrit le WAV et répond « ok » sur stdout.
Lancé par engine/voice.py avec le Python de l'environnement Parler
(voir engine/setup_parler.sh), pour garder le modèle chargé entre les répliques."""
import json
import sys

import numpy as np
import soundfile as sf
import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer

M = "parler-tts/parler-tts-mini-multilingual-v1.1"
model = ParlerTTSForConditionalGeneration.from_pretrained(M)
tok = AutoTokenizer.from_pretrained(M)
dtok = AutoTokenizer.from_pretrained(model.config.text_encoder._name_or_path)
print("pret", flush=True)
for raw in sys.stdin:
    req = json.loads(raw)
    torch.manual_seed(int(req.get("seed", 1)))
    d = dtok(req["desc"], return_tensors="pt")
    t = tok(req["text"], return_tensors="pt")
    a = model.generate(input_ids=d.input_ids, attention_mask=d.attention_mask,
                       prompt_input_ids=t.input_ids, prompt_attention_mask=t.attention_mask)
    a = np.atleast_1d(a.cpu().numpy().squeeze()).astype(np.float32)
    if a.size < 1000:   # tirage raté (presque vide) : on renvoie un silence court,
        a = np.zeros(1000, np.float32)  # le contrôle de débit du moteur refait la réplique
    sf.write(req["out"], a, model.config.sampling_rate)
    print("ok", flush=True)
