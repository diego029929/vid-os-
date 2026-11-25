---
name: voix-pocket-tts
description: Voix off française gratuite et locale avec Kyutai Pocket TTS (voix « estelle »), le narrateur de toutes les vidéos depuis le 22/11. À lire avant de générer, vérifier ou changer une voix off (engine/voice.py, nuit.py, vidéos 3D).
---

# Voix off : Kyutai Pocket TTS (narratrice depuis le 22/11)

Fio, 22/11 nuit : « la voix est nulle, installe un skill pour les voix, à toi de choisir ».
Choix : **Kyutai Pocket TTS** (modèle `french`, voix native **`estelle`**), gratuit, open source,
tourne sur CPU (≈ 1 s de calcul par phrase après le chargement), sans clé ni compte.
Bien plus naturel que Piper (fini l'effet mégaphone).

## Installer (dans chaque conteneur)
```bash
pip install -q pocket-tts        # le modèle (≈ 300 Mo) se télécharge seul depuis huggingface.co au 1er appel
```
`sh engine/get_voice.sh` le fait aussi quand `voice_config.json` dit `"voice": "pocket"`.

## Utiliser
- **Moteur du dépôt (recommandé)** : `engine/voice.py` lit `engine/voice_config.json`
  (`"voice": "pocket"`, `"pocket_voice": "estelle"`, `"effect": "leger"`, `"tempo": 0.92`).
  `voice.synth(texte)` → audio 44,1 kHz ; `voice.megaphone(audio, tmp)` applique l'effet de la config
  (« leger » = juste un peu de présence). `engine/nuit.py` l'utilise tout seul.
- **En ligne de commande** : `pocket-tts generate --language french --voice estelle --text "…" --output-path a.wav`
- **En Python** :
  ```python
  from pocket_tts import TTSModel
  m = TTSModel.load_model(language="french"); st = m.get_state_for_audio_prompt("estelle")
  audio = m.generate_audio(st, "Phrase.").numpy()   # m.sample_rate = 24000
  ```

## Règles
- **Une phrase à la fois**, puis **vérifier chaque phrase avec Whisper** (faster-whisper `small`
  ou openai-whisper `medium`) ; refaire la phrase si un mot est faux (le tirage change à chaque appel),
  changer la tournure si elle échoue 2 fois. Whisper oublie souvent un mot d'une syllabe en tout début
  (« Faux. ») : écouter/découper avant de conclure.
- Pocket parle vite : `tempo` 0.92 (ralenti sans changer la hauteur). Ne JAMAIS baisser la hauteur.
- Autres voix du modèle français (non natives, accent possible) : `fantine`, `anna`, `cosette`
  (femmes), `jean`, `javert` (hommes graves). Le clonage d'une voix (fichier wav) demande un compte
  Hugging Face : ne PAS le faire, et jamais la voix d'un autre créateur.
- Minutage des mots pour les sous-titres : Whisper `word_timestamps=True` sur chaque phrase.
  Avec faster-whisper, passer l'audio en numpy 16 kHz (la lecture de fichier par `av` plante ici).
- Revenir à l'ancienne voix : `voice_config.json` → `"voice": "fr_FR-upmc-medium"`, `"effect": "megaphone"`, `"tempo": 1.1`.

Licence : pocket-tts (Kyutai), code MIT, poids CC-BY 4.0 (usage commercial permis).
