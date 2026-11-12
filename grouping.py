#!/usr/bin/env python3
"""Vorfall-Gruppierung ohne Claude: gleiche Ereignisse in mehreren Meldungen (auch verschiedene Sprachen) werden über
Satz-Embeddings (mehrsprachiges MiniLM, läuft lokal auf dem Runner, kostenlos) gefunden.
Gruppiert wird nur, wenn: Ähnlichkeit hoch (Durchschnitt über die ganze Gruppe), höchstens 2 Tage Abstand, gleiches Land
(oder bei einer Seite kein Land), Gruppengröße begrenzt."""
import datetime as dt

import numpy as np

MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def embed(texts):
    from fastembed import TextEmbedding
    vecs = np.array(list(TextEmbedding(MODEL).embed(texts)), dtype=np.float32)
    return vecs / np.linalg.norm(vecs, axis=1, keepdims=True)


def clusters(vecs, times, countries, thr=0.72, max_size=8, max_hours=48):
    """Durchschnitts-Verknüpfung (average linkage) mit Nebenbedingungen. Gibt Listen von Indizes zurück (nur Größe >= 2)."""
    n = len(vecs)
    S = vecs @ vecs.T
    dh = np.abs(times[:, None] - times[None, :]) / 3600.0
    ok = dh <= max_hours
    for a in range(n):
        for b in range(a + 1, n):
            ca, cb = countries[a], countries[b]
            if ca and cb and not (ca & cb):
                ok[a, b] = ok[b, a] = False
    M = np.where(ok, S, -1.0).astype(np.float64)       # unzulässige Paare ziehen den Durchschnitt unter die Schwelle
    np.fill_diagonal(M, 0.0)
    size = np.ones(n)
    members = {k: [k] for k in range(n)}
    active = np.ones(n, dtype=bool)
    avg = M.copy()
    np.fill_diagonal(avg, -np.inf)
    while True:
        k = int(np.argmax(avg))
        i, j = divmod(k, n)
        if avg[i, j] < thr:
            break
        if size[i] + size[j] > max_size:
            avg[i, j] = avg[j, i] = -np.inf
            continue
        M[i, :] += M[j, :]
        M[:, i] += M[:, j]
        size[i] += size[j]
        members[i] += members.pop(j)
        active[j] = False
        avg[j, :] = avg[:, j] = -np.inf
        for m in np.flatnonzero(active):
            if m != i:
                avg[i, m] = avg[m, i] = M[i, m] / (size[i] * size[m])
    return [v for v in members.values() if len(v) >= 2]


def group_items(items, days=3, thr=0.72, max_size=8, embedder=embed):
    """Setzt item['grp'] für relevante Meldungen der letzten Tage neu; ältere behalten ihre Gruppe. Gibt die Zahl der Gruppen zurück."""
    cut = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).isoformat()
    live = [i for i in items if (i.get("ai") or {}).get("relevant") and i["published"] >= cut]
    if len(live) < 2:
        return 0
    vecs = embedder([(i.get("title_de") or i["title_orig"]) for i in live])
    times = np.array([dt.datetime.fromisoformat(i["published"]).timestamp() for i in live])
    ctry = [set((i.get("ai") or {}).get("countries") or []) for i in live]
    cl = clusters(vecs, times, ctry, thr=thr, max_size=max_size)
    for i in live:
        i.pop("grp", None)
    for c in cl:
        tag = "g" + min(live[k]["id"] for k in c)
        for k in c:
            live[k]["grp"] = tag
    return len(cl)
