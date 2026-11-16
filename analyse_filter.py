"""Einmalig: Welche Stichwortgruppen sagen voraus, ob Claude eine Meldung relevant findet? (nur Zahlen)"""
import collections, datetime as dt, re
import build
cfg = build.CFG
news = build.load("news.json")
now = dt.datetime.now(dt.timezone.utc)
items = [i for i in news["items"] if (now - dt.datetime.fromisoformat(i["published"])).days < 8]
judged = [i for i in items if (i.get("ai") or {}).get("model") not in (None, "prefilter")]
rel = lambda i: bool(i["ai"].get("relevant"))
print("Fenster", len(items), "von Claude beurteilt", len(judged), "relevant", sum(map(rel, judged)))
text = lambda i: f'{i["title_orig"]} {i.get("title_de") or ""} {i.get("snippet") or ""}'
groups = {}
for r in cfg["rubrics"]:
    for k in ("must", "core"):
        if r.get(k):
            groups[f'{r["id"]}.{k}'] = re.compile(r[k], re.I)
for k in ("events", "boost", "radar"):
    if cfg.get(k):
        groups[k] = re.compile(cfg[k], re.I)
def tags(i):
    t = text(i)
    return frozenset(g for g, rx in groups.items() if rx.search(t))
rows = collections.defaultdict(lambda: [0, 0])
for i in judged:
    for g in tags(i) or {"keine"}:
        rows[g][0] += 1; rows[g][1] += rel(i)
print("--- je Gruppe (n, relevant, Quote)")
for g, (n, r) in sorted(rows.items(), key=lambda kv: -kv[1][0]):
    print(f"{g:22s} {n:5d} {r:5d} {r / n:5.0%}")
combo = collections.defaultdict(lambda: [0, 0])
for i in judged:
    combo[tuple(sorted(tags(i)))][0] += 1; combo[tuple(sorted(tags(i)))][1] += rel(i)
print("--- nur genau diese Kombination (n, relevant)")
for c, (n, r) in sorted(combo.items(), key=lambda kv: -kv[1][0])[:14]:
    print(f"{n:5d} {r:4d} {r / n:4.0%}  {','.join(c) or 'keine'}")
for key in ("open", "trusted", "kunde"):
    for v in (True, False):
        s = [i for i in judged if bool(i.get(key)) == v]
        print(key, v, len(s), "relevant", sum(map(rel, s)))
lang = collections.defaultdict(lambda: [0, 0])
for i in judged:
    lang[i["lang"]][0] += 1; lang[i["lang"]][1] += rel(i)
print("Sprache:", {k: tuple(v) for k, v in lang.items()})
no_c = [i for i in judged if not i.get("countries")]
print("ohne Land:", len(no_c), "relevant", sum(map(rel, no_c)))
unj = [i for i in items if not i.get("ai")]
print("unbeurteilt", len(unj), "davon ohne jede Gruppe", sum(1 for i in unj if not tags(i)), "open", sum(1 for i in unj if i.get("open")))
