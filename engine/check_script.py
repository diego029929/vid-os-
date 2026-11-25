"""Relecture orthographe + grammaire d'un épisode avant le rendu (LanguageTool, gratuit, hors ligne).

Usage : python3 engine/check_script.py episodes/epNN.json [autres.json ...]

Installation (une fois par session, ≈ 30 s, Java déjà présent) :
    pip install -q language_tool_python
Le premier lancement télécharge LanguageTool (≈ 260 Mo) dans ~/.cache.

Les textes à l'écran sont en MAJUSCULES : LanguageTool ne voit pas les fautes
dans ce cas, donc on les remet en minuscules (majuscule en début de phrase).
- « FAUTE »   : grammaire / conjugaison / accord → à corriger avant le rendu
                (code de sortie 1).
- « À VOIR »  : mot inconnu (souvent un nom propre) → vérifier, pas bloquant.
"""
import json
import re
import sys

# règles de présentation : sans intérêt pour des sous-titres en majuscules
# (CAT_TOURS_CRITIQUES = tournures « familières » : voulues sur TikTok)
IGNORE_CAT = {"TYPOGRAPHY", "PUNCTUATION", "PONCTUATION_VIRGULE", "CASING", "STYLE", "REDUNDANCY",
              "TYPOS_AUTO", "CAT_TOURS_CRITIQUES"}
IGNORE_RULE = {"WHITESPACE_RULE", "FRENCH_WHITESPACE", "APOS_TYP", "UPPERCASE_SENTENCE_START",
               "DOUBLE_PUNCTUATION", "ESPACE_APRES_POINT", "FR_UNPAIRED_BRACKETS", "UNPAIRED_BRACKETS",
               "POINT_VIRGULE_PREMIUM", "VIRG_NON_TROUVEE", "TIRET", "ELISION"}
SPELL = {"FR_SPELLING_RULE", "HUNSPELL_RULE", "MORFOLOGIK_RULE_FR"}


def lines(ep):
    """Toutes les phrases lues ou affichées : texte, voix, choix A/B."""
    for i, b in enumerate(ep.get("beats", [])):
        for key in ("voice", "text"):
            if b.get(key):
                yield i + 1, b[key]
        c = b.get("choice") or {}
        for key in ("a", "b"):
            if c.get(key):
                yield i + 1, c[key]
    for key in ("caption", "title", "question"):
        if isinstance(ep.get(key), str):
            yield 0, ep[key]


def sentence_case(t):
    t = re.sub(r"#\w+", "", t.replace("*", ""))
    if t.upper() != t:          # déjà en minuscules : on ne touche à rien
        return t
    t = t.lower()
    return re.sub(r"(^|[.!?«…]\s*)([a-zà-ÿ])", lambda m: m.group(1) + m.group(2).upper(), t)


def main(paths):
    import language_tool_python
    try:
        tool = language_tool_python.LanguageTool("fr")
    except Exception as e:  # pas de Java ou pas de réseau : API publique gratuite (20 requêtes/min)
        print(f"LanguageTool local indisponible ({e}), API publique utilisée")
        tool = language_tool_python.LanguageToolPublicAPI("fr")
    fautes = 0
    for path in paths:
        with open(path) as fh:
            ep = json.load(fh)
        seen = set()
        for n, raw in lines(ep):
            txt = sentence_case(raw)
            if txt in seen:
                continue
            seen.add(txt)
            for m in tool.check(txt):
                if m.category in IGNORE_CAT or m.rule_id in IGNORE_RULE:
                    continue
                mot = txt[m.offset:m.offset + m.error_length]
                sugg = ", ".join(m.replacements[:3])
                if m.rule_id in SPELL:
                    if any(r.lower() == mot.lower() for r in m.replacements):
                        continue        # nom propre en minuscules (léa → Léa) : pas une faute
                    print(f"  À VOIR {path} plan {n} : « {mot} » ({sugg or 'mot inconnu'})")
                else:
                    fautes += 1
                    print(f"  FAUTE  {path} plan {n} : « {txt} »\n         {m.message} → {sugg}")
    tool.close()
    print(f"relecture : {fautes} faute(s)" + (" — corriger avant le rendu" if fautes else " — OK"))
    return 1 if fautes else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
