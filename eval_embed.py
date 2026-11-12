#!/usr/bin/env python3
"""Einmaliger Test: Wie gut finden Embeddings dieselben Vorfälle wie Claude? Gibt NUR Zahlen aus (das Log ist öffentlich)."""
import datetime as dt
import json
import sys
import time
from pathlib import Path

import numpy as np

t0 = time.time()
d = json.loads((Path(__file__).parent / "data" / "news.json").read_text(encoding="utf-8"))
cut = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=3)).isoformat()
live = [i for i in d["items"] if (i.get("ai") or {}).get("relevant") and i["published"] >= cut]
truth = {}
for i in live:
    g = i.get("grp")
    if isinstance(g, str) and g.startswith("g"):
        truth.setdefault(g, []).append(i["id"])
truth = {g: v for g, v in truth.items() if len(v) >= 2}
print(f"relevante Meldungen (3 Tage): {len(live)}; Claude-Gruppen: {len(truth)} mit {sum(len(v) for v in truth.values())} Meldungen")

from fastembed import TextEmbedding
t1 = time.time()
model = TextEmbedding("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
print(f"Modell geladen in {time.time() - t1:.0f} s")
texts = [(i.get("title_de") or i["title_orig"]) for i in live]
t2 = time.time()
E_ = np.array(list(model.embed(texts)))
E_ /= np.linalg.norm(E_, axis=1, keepdims=True)
print(f"{len(texts)} Titel eingebettet in {time.time() - t2:.1f} s")
S = E_ @ E_.T
ids = [i["id"] for i in live]
pos = {k: n for n, k in enumerate(ids)}
tp_pairs = set()
for v in truth.values():
    for a in range(len(v)):
        for b in range(a + 1, len(v)):
            tp_pairs.add(tuple(sorted((pos[v[a]], pos[v[b]]))))
print(f"Paare laut Claude: {len(tp_pairs)}")
sizes = sorted((len(v) for v in truth.values()), reverse=True)
print("Gruppengrößen laut Claude:", sizes)
for g, v in sorted(truth.items(), key=lambda kv: -len(kv[1]))[:6]:
    ix = [pos[x] for x in v]
    sub = S[np.ix_(ix, ix)]
    mean = (sub.sum() - len(ix)) / (len(ix) * (len(ix) - 1))
    items_ = [live[k] for k in ix]
    print(f"  Gruppe mit {len(v)}: mittlere Ähnlichkeit {mean:.2f}; Rubriken {sorted({(i.get('ai') or {}).get('rubric') for i in items_})}; Quellen {len({i['source'] for i in items_})}")
big = max(truth.values(), key=len)
bi = [live[pos[x]] for x in big]
import collections
print("Riesengruppe: Sprachen", dict(collections.Counter(i["lang"] for i in bi)))
print("Riesengruppe: Tage", dict(sorted(collections.Counter(i["published"][:10] for i in bi).items())))
print("Riesengruppe: Länderzahl je Meldung", dict(collections.Counter(len((i.get("ai") or {}).get("countries") or []) for i in bi)))
print("Riesengruppe: mit firma/kunde", sum(1 for i in bi if i.get("firma") is not None), sum(1 for i in bi if i.get("kunde")))
print("Riesengruppe: Tag-Schlüssel", sorted({i["grp"] for i in bi}), "min-id-Länge", min(len(x) for x in big))
sys.path.insert(0, str(Path(__file__).parent))
import build
cards, top, sections, _ = build.compute(d["items"], dt.datetime.now(dt.timezone.utc))
print("Karten:", len(cards), "größte Quellenzahlen:", sorted((c["n"] for c in cards), reverse=True)[:8])
print("Rubrik-Verteilung der Karten:", dict(collections.Counter(c["rubric"] for c in cards)))
iu = np.triu_indices(len(ids), 1)
for t in (0.60, 0.65, 0.70, 0.75, 0.80, 0.85):
    hit = S[iu] >= t
    pred = {(int(a), int(b)) for a, b in zip(iu[0][hit], iu[1][hit])}
    tp = len(pred & tp_pairs)
    p = tp / len(pred) if pred else 0
    r = tp / len(tp_pairs) if tp_pairs else 0
    f = 2 * p * r / (p + r) if p + r else 0
    print(f"Schwelle {t:.2f}: Paare {len(pred):4d}  Präzision {p:.2f}  Trefferquote {r:.2f}  F1 {f:.2f}")
print(f"gesamt {time.time() - t0:.0f} s")
