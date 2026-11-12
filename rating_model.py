#!/usr/bin/env python3
"""Lernt aus deinen Ampel-Bewertungen, ohne Claude und ohne Kosten: Meldungen, die bewerteten Meldungen inhaltlich ähneln
(mehrsprachige Embeddings), bekommen deren Tendenz: ähnlich zu Grün → nach oben, ähnlich zu Rot/Gelb → nach unten,
bei sehr großer Ähnlichkeit zu Rot → ausgeblendet. Gibt je Meldung eine Zahl von -1 (unpassend) bis +1 (passend) zurück."""
import datetime as dt
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent
VALUE = dict(g=1.0, y=-0.4, r=-1.0)


def load_ratings():
    f = ROOT / "data" / "ratings.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _predict(sims, vals, min_sim, k):
    """sims: Ähnlichkeiten zu bewerteten Meldungen; Rückgabe (Tendenz, Zahl der Nachbarn)."""
    idx = np.flatnonzero(sims >= min_sim)
    if not len(idx):
        return 0.0, 0
    idx = idx[np.argsort(-sims[idx])][:k]
    w = sims[idx] ** 4
    return float((w * vals[idx]).sum() / (w.sum() + 0.35)), len(idx)


def annotate(items, window_days=7, min_sim=0.62, k=5, min_ratings=20, embedder=None, quiet=False):
    """Liefert {id: Tendenz} für Meldungen der letzten Tage; prüft sich selbst per Leave-one-out und gibt Trefferzahlen aus."""
    ratings = load_ratings()
    by = {i["id"]: i for i in items}
    rated = [(by[k_], v["r"]) for k_, v in ratings.items() if k_ in by and v.get("r") in VALUE]
    if len(rated) < min_ratings:
        if not quiet:
            print(f"Ampel-Modell: nur {len(rated)} bewertete Meldungen im Archiv, Start ab {min_ratings}")
        return {}
    cut = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=window_days)).isoformat()
    cand = [i for i in items if (i.get("ai") or {}).get("relevant", True) and i["published"] >= cut]
    if embedder is None:
        import grouping
        embedder = grouping.embed
    rid = {i["id"] for i, _ in rated}
    pool = rated_items = [i for i, _ in rated]
    extra = [i for i in cand if i["id"] not in rid]
    vecs = embedder([(i.get("title_de") or i["title_orig"]) for i in pool + extra])
    R, X = vecs[:len(pool)], vecs[len(pool):]
    vals = np.array([VALUE[lab] for _, lab in rated])
    # Selbsttest: jede bewertete Meldung wird ohne sich selbst vorhergesagt
    S = R @ R.T
    np.fill_diagonal(S, -1.0)
    ok = tot = 0
    for n in range(len(rated)):
        t, c = _predict(S[n], vals, min_sim, k)
        if c:
            tot += 1
            ok += (t > 0) == (vals[n] > 0)
    out = {}
    for n, i in enumerate(extra):
        t, c = _predict(X[n] @ R.T, vals, min_sim, k)
        if c:
            out[i["id"]] = t
    for n, i in enumerate(rated_items):
        t, c = _predict(S[n], vals, min_sim, k)
        if c:
            out[i["id"]] = t
    if not quiet:
        print(f"Ampel-Modell: {len(rated)} Bewertungen; Selbsttest: {tot} mit Nachbarn, davon {ok} richtig ({round(100 * ok / tot) if tot else 0} %); "
              f"{len(out)} von {len(cand)} Meldungen mit Tendenz, {sum(1 for v in out.values() if v <= -0.6)} stark negativ")
    return out
