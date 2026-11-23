#!/usr/bin/env python3
"""Plan du jour piloté par les stats (demande de Fio, 21/11 : « tu publies tout le temps la même chose,
fais évoluer les vidéos comme tu le calcules pour les follows »).

Usage : python3 engine/plan.py [AAAA-MM-JJ] [--hors-ligne stats.json]
  - lit les stats Zernio (GET /v1/analytics, toutes les pages), relie chaque post à series/state.json → published
    (zernio_id) et à son JSON d'épisode (champs "format", "ambiance", "accroche") ;
  - donne un score à chaque vidéo (abonnés gagnés d'abord, puis rétention, likes, commentaires/partages, vues) ;
  - garde ce qui marche, teste 1 à 2 nouveautés par jour, coupe ce qui ne marche pas (7 jours de pause),
    et évite de répéter la même forme (format / ambiance / accroche) ;
  - écrit series/plans/AAAA-MM-JJ.json et affiche le plan en français.
La routine (ROUTINE.md § 0 bis) suit ce plan créneau par créneau.
"""
import json, os, sys, random, datetime as dt, urllib.request, statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "series", "state.json")
FORMATS = os.path.join(ROOT, "series", "formats.json")
PLANS = os.path.join(ROOT, "series", "plans")

SLOTS_NUIT = ["12:00", "17:00", "20:00"]  # 23/11 (Fio) : 3 vidéos/jour, espacées (TikTok bloquait 4 vidéos sur 6)
MAX_SERIES = 1          # 22/11 : les vidéos virales sont des histoires COMPLÈTES de ~30 s ; 1 série au plus
MAX_TESTS = 2           # nouveautés par jour
MIN_AGE_H = 20          # stats trop jeunes avant ça
MIN_VUES = 30           # en dessous : vidéo non diffusée par TikTok (bloquée), pas notée
COUPE_JOURS = 7
POIDS = {"portee": 0.30, "retention": 0.30, "abonnes": 0.20, "likes": 0.10, "interaction": 0.10}  # 21/11 : objectif de Fio = 1 000 vues par vidéo


def zernio_posts():
    key = os.environ.get("ZERNIO_API_KEY")
    if not key:
        sys.exit("ZERNIO_API_KEY manquante")
    out, page = [], 1
    while True:
        req = urllib.request.Request(f"https://zernio.com/api/v1/analytics?limit=100&page={page}",
                                     headers={"Authorization": f"Bearer {key}"})
        d = json.load(urllib.request.urlopen(req, timeout=60))
        out += d.get("posts", [])
        if page >= d.get("pagination", {}).get("pages", 1):
            return out
        page += 1


def tags_of(pub):
    """format / ambiance / accroche d'une vidéo publiée (JSON d'épisode, sinon déduit de l'historique)."""
    ep = {}
    f = pub.get("file")
    if f and os.path.exists(os.path.join(ROOT, f)):
        try:
            ep = json.load(open(os.path.join(ROOT, f)))
        except Exception:
            ep = {}
    series = pub.get("series", "")
    fmt = pub.get("format") or ep.get("format")
    if not fmt:
        if series.startswith("gta6"):
            fmt = "edit" if ("edit" in str(pub.get("episode")) or "edit" in (f or "")) else "gta-dessin"
        elif ep.get("style") == "nuit":
            fmt = "serie"
        else:
            fmt = "ancien"
    amb = pub.get("ambiance") or ep.get("ambiance") or ("nuit" if ep.get("style") == "nuit" else None)
    acc = pub.get("accroche") or ep.get("accroche")
    return fmt, amb, acc


def metrics(rows):
    """rows = posts Zernio d'un même zernio_id (TikTok + Instagram)."""
    tk = next((r for r in rows if r["platform"] == "tiktok"), None)
    ig = next((r for r in rows if r["platform"] == "instagram"), None)
    a, b = (tk or {}).get("analytics", {}) or {}, (ig or {}).get("analytics", {}) or {}
    v_tk, v_ig = a.get("views") or 0, b.get("views") or 0
    if v_tk + v_ig == 0:
        return None
    ret = []
    for x in (a, b):
        d, w = x.get("videoDurationSeconds") or 0, x.get("igReelsAvgWatchTime") or 0
        if d and w and (x.get("views") or 0) >= MIN_VUES:
            ret.append(min(1.0, w / 1000 / d))
    v = v_tk + v_ig
    return {
        "bloquee": tk is not None and v_tk < MIN_VUES,
        "abonnes": (a.get("follows") or 0) / max(v_tk, 1) * 1000,
        "retention": sum(ret) / len(ret) if ret else 0,
        "likes": ((a.get("likes") or 0) + (b.get("likes") or 0)) / v,
        "interaction": sum((x.get(k) or 0) for x in (a, b) for k in ("comments", "shares", "saves")) / v,
        "portee": v,
        "vues_tk": v_tk, "vues_ig": v_ig, "follows": a.get("follows") or 0,
        "commentaires": (a.get("comments") or 0) + (b.get("comments") or 0),
        "publie": (tk or ig).get("publishedAt"),
    }


def pct_rank(vals):
    s = sorted(vals)
    return lambda x: (sum(1 for y in s if y < x) + 0.5 * sum(1 for y in s if y == x)) / len(s)


def score_all(videos):
    ok = [v for v in videos if not v["m"]["bloquee"]]
    if not ok:
        return
    ranks = {k: pct_rank([v["m"][k] for v in ok]) for k in POIDS}
    for v in videos:
        v["score"] = None if v["m"]["bloquee"] else round(sum(w * ranks[k](v["m"][k]) for k, w in POIDS.items()), 3)


def stats_par(videos, key, depuis):
    g = defaultdict(list)
    for v in videos:
        if v["score"] is not None and v[key] and v["date"] >= depuis:
            g[v[key]].append(v["score"])
    return {k: (statistics.mean(s), len(s)) for k, s in g.items()}


def pick(rng, candidats, stats, exclus, explore=True):
    """Choix pondéré : jamais testé = bonus d'exploration ; sinon exp(score). exclus = à éviter si possible."""
    pool = [c for c in candidats if c not in exclus] or list(candidats)
    w = []
    for c in pool:
        m, n = stats.get(c, (None, 0))
        if n == 0:
            w.append(3.0 if explore else 0.5)
        else:
            w.append(2.718 ** (4 * m) * (1.6 if n < 3 else 1.0))
    return rng.choices(pool, weights=w)[0]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    jour = dt.date.fromisoformat(args[0]) if args else dt.date.today() + dt.timedelta(days=0)
    rng = random.Random(jour.toordinal())
    state = json.load(open(STATE))
    cat = json.load(open(FORMATS))
    formats = {k: v for k, v in cat["formats"].items() if v.get("statut") == "actif"}
    ambiances = [k for k in cat["ambiances"] if not k.startswith("_")]
    accroches = [k for k in cat["accroches"] if not k.startswith("_")]

    if "--hors-ligne" in sys.argv:
        posts = json.load(open(sys.argv[sys.argv.index("--hors-ligne") + 1]))
    else:
        posts = zernio_posts()
    by_id = defaultdict(list)
    for p in posts:
        by_id[p.get("latePostId") or p.get("_id")].append(p)

    now = dt.datetime.now(dt.timezone.utc)
    videos = []
    for pub in state.get("published", []):
        rows = by_id.get(pub.get("zernio_id"))
        if not rows:
            continue
        m = metrics(rows)
        if not m or not m["publie"]:
            continue
        t = dt.datetime.fromisoformat(m["publie"].replace("Z", "+00:00"))
        fmt, amb, acc = tags_of(pub)
        videos.append({"pub": pub, "m": m, "age_h": (now - t).total_seconds() / 3600, "date": t.date(),
                       "format": fmt, "ambiance": amb, "accroche": acc, "series": pub.get("series"),
                       "slot": (pub.get("slot") or "")[11:16]})
    mures = [v for v in videos if v["age_h"] >= MIN_AGE_H]
    score_all(mures)
    for v in videos:
        v.setdefault("score", None)
    depuis = jour - dt.timedelta(days=14)
    s_fmt = stats_par(mures, "format", depuis)
    s_amb = stats_par(mures, "ambiance", depuis)
    s_acc = stats_par(mures, "accroche", depuis)
    tous = [v["score"] for v in mures if v["score"] is not None and v["date"] >= depuis]
    seuil_bas = sorted(tous)[len(tous) // 3] if len(tous) >= 6 else 0

    # --- coupes (7 jours) : format / ambiance / accroche notés ≥ 4 fois (≥ 3 pour les variantes) et dans le tiers du bas
    var = state.setdefault("variation", {})
    coupes = var.setdefault("coupes", {})
    for nom, (m, n) in s_fmt.items():
        if nom in formats and nom != "edit" and n >= 4 and m < seuil_bas and nom not in coupes:
            coupes[nom] = {"jusqu_au": str(jour + dt.timedelta(days=COUPE_JOURS)), "score": round(m, 2), "n": n}
    for st in (s_amb, s_acc):
        for nom, (m, n) in st.items():
            if n >= 3 and m < seuil_bas and nom not in coupes:
                coupes[nom] = {"jusqu_au": str(jour + dt.timedelta(days=COUPE_JOURS)), "score": round(m, 2), "n": n}
    for nom in list(coupes):
        if dt.date.fromisoformat(coupes[nom]["jusqu_au"]) < jour:
            del coupes[nom]          # fin de la pause : peut être re-testé
    actifs = [f for f in formats if f not in coupes and f != "edit"]
    amb_ok = [a for a in ambiances if a not in coupes]
    acc_ok = [a for a in accroches if a not in coupes]

    # --- ce qui a été publié hier (à ne pas répéter)
    hier = jour - dt.timedelta(days=1)
    plan_hier = {}
    ph = os.path.join(PLANS, f"{hier}.json")
    if os.path.exists(ph):
        plan_hier = {c["heure"]: c for c in json.load(open(ph)).get("creneaux", [])}
    hier_vals = defaultdict(set)
    for c in plan_hier.values():
        for k in ("format", "ambiance", "accroche"):
            if c.get(k):
                hier_vals[k].add(c[k])

    # --- séries en cours : on garde les 2 meilleures, les autres s'arrêtent
    en_cours = [s for s in state.get("parallel_series", []) if s.get("next_episode", 99) <= s.get("episode_count", 3)]
    def score_serie(s):
        sc = [v["score"] for v in videos if v["series"] == s["series"] and v["score"] is not None]
        bloq = any(v["m"]["bloquee"] for v in videos if v["series"] == s["series"] and v["age_h"] >= 6)
        jeunes = [v for v in videos if v["series"] == s["series"] and v["score"] is None and not v["m"]["bloquee"]]
        if sc:
            return statistics.mean(sc) - (0.2 if bloq else 0)
        if jeunes:   # trop jeune : on estime avec les likes/rétention bruts comparés aux autres séries du jour
            m = jeunes[-1]["m"]
            return 0.5 * min(1, m["retention"] * 5) + 0.5 * min(1, m["likes"] * 10) - (0.4 if bloq else 0)
        return -1 if bloq else 0.4
    en_cours.sort(key=score_serie, reverse=True)
    gardees, arretees = en_cours[:MAX_SERIES], en_cours[MAX_SERIES:]

    creneaux = []
    for h in ["08:00", "09:00"]:
        if "edit" in formats:
            creneaux.append({"heure": h, "format": "edit", "moteur": "edit",
                             "consigne": "Edit GTA 6, thème jamais traité (§ 1 ter).", "raison": "créneau fixe (demande de Fio)"})
    libres = list(SLOTS_NUIT)
    for s in gardees:
        h = s["slot"] if s["slot"] in libres else libres[0]
        libres.remove(h)
        last = s.get("next_episode") == s.get("episode_count")
        amb = s.get("ambiance") or "nuit"
        acc = pick(rng, acc_ok, s_acc, hier_vals["accroche"] | {c.get("accroche") for c in creneaux})
        creneaux.append({"heure": h, "format": "serie", "moteur": "nuit", "series": s["series"], "prefix": s["prefix"],
                         "partie": s["next_episode"], "derniere": last, "ambiance": amb, "accroche": acc,
                         "raison": f"série gardée (score {score_serie(s):.2f}), partie {s['next_episode']}/{s['episode_count']}"})

    # --- créneaux libres : 1-2 nouveautés (formats / variantes jamais ou peu testés) + le meilleur format connu
    tests = 0
    deja = {c["format"] for c in creneaux if c["format"] != "serie"}
    nb_series = len(gardees)
    for h in libres:
        cand = [f for f in actifs if f not in deja]
        if nb_series >= MAX_SERIES:
            cand = [f for f in cand if f != "serie"]
        jamais = [f for f in cand if s_fmt.get(f, (0, 0))[1] < 2]
        if jamais and tests < MAX_TESTS:
            fmt = pick(rng, jamais, s_fmt, hier_vals["format"])
            tests += 1
            raison = "NOUVEAUTÉ à tester (pas encore assez de stats)"
        else:
            connus = [f for f in cand if s_fmt.get(f, (0, 0))[1] >= 2] or cand
            fmt = pick(rng, connus, s_fmt, hier_vals["format"], explore=False)
            m, n = s_fmt.get(fmt, (0, 0))
            raison = f"format qui marche (score moyen {m:.2f} sur {n} vidéos)" if n else "rotation"
        deja.add(fmt)
        if fmt == "serie":
            nb_series += 1
        used_amb = {c.get("ambiance") for c in creneaux}
        used_acc = {c.get("accroche") for c in creneaux}
        amb = pick(rng, amb_ok, s_amb, hier_vals["ambiance"] | used_amb)
        acc = pick(rng, acc_ok, s_acc, hier_vals["accroche"] | used_acc)
        if fmt == "regles":
            acc = "regle_affichee"
        c = {"heure": h, "format": fmt, "moteur": formats[fmt]["moteur"], "ambiance": amb, "accroche": acc,
             "duree": formats[fmt]["duree"], "raison": raison}
        if fmt == "serie":
            c.update({"partie": 1, "nouvelle_serie": True})
        creneaux.append(c)
    creneaux.sort(key=lambda c: c["heure"])

    # --- bilan lisible
    top = sorted([v for v in mures if v["score"] is not None and v["date"] >= jour - dt.timedelta(days=7)],
                 key=lambda v: v["score"], reverse=True)
    plan = {
        "jour": str(jour),
        "creneaux": creneaux,
        "series_arretees": [{"series": s["series"], "slot": s["slot"],
                             "raison": f"moins bonne que la ou les {MAX_SERIES} gardée(s) (max {MAX_SERIES} série à la fois)"} for s in arretees],
        "coupes": coupes,
        "scores_formats": {k: {"score": round(m, 3), "videos": n} for k, (m, n) in s_fmt.items()},
        "scores_ambiances": {k: {"score": round(m, 3), "videos": n} for k, (m, n) in s_amb.items()},
        "scores_accroches": {k: {"score": round(m, 3), "videos": n} for k, (m, n) in s_acc.items()},
        "meilleures_7j": [{"fichier": v["pub"].get("file"), "score": v["score"], "follows": v["m"]["follows"],
                           "vues": v["m"]["vues_tk"] + v["m"]["vues_ig"], "retention": round(v["m"]["retention"], 3)}
                          for v in top[:5]],
        "objectif_1000_vues_7j": f"{sum(1 for v in videos if v['m']['vues_tk'] >= 1000 and v['date'] >= jour - dt.timedelta(days=7))} vidéo(s) sur {sum(1 for v in videos if v['date'] >= jour - dt.timedelta(days=7))} ont passé 1 000 vues TikTok",
        "bloquees_7j": [v["pub"].get("file") for v in videos if v["m"]["bloquee"] and v["date"] >= jour - dt.timedelta(days=7)
                        and v["age_h"] >= 6],
    }
    os.makedirs(PLANS, exist_ok=True)
    json.dump(plan, open(os.path.join(PLANS, f"{jour}.json"), "w"), ensure_ascii=False, indent=1)
    var["dernier_plan"] = str(jour)
    json.dump(state, open(STATE, "w"), ensure_ascii=False, indent=1)

    print(f"PLAN DU {jour}")
    for c in creneaux:
        extra = f" · {c['series']} partie {c['partie']}{' (DERNIÈRE)' if c.get('derniere') else ''}" if c.get("series") else ""
        print(f"  {c['heure']}  {c['format']:<9}{extra}  ambiance={c.get('ambiance', '-')}  accroche={c.get('accroche', '-')}  → {c['raison']}")
    for s in plan["series_arretees"]:
        print(f"  ARRÊTÉE : {s['series']} ({s['raison']})")
    if coupes:
        print("  En pause 7 jours :", ", ".join(f"{k} (jusqu'au {v['jusqu_au']})" for k, v in coupes.items()))
    print("  Objectif Fio :", plan["objectif_1000_vues_7j"])
    print("  Scores formats :", plan["scores_formats"])
    if plan["bloquees_7j"]:
        print("  Bloquées par TikTok (< 30 vues) :", plan["bloquees_7j"])


if __name__ == "__main__":
    main()
