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
import ai
pre = ai._prefilter()
kept = [i for i in judged if pre.search(text(i)) or i.get("trusted")]
lost = [i for i in judged if i not in kept]
print("beurteilte", len(judged), "behalten", len(kept), "verworfen", len(lost), "davon relevant", sum(map(rel, lost)), "von relevant gesamt", sum(map(rel, judged)))
rub = collections.Counter(i["ai"].get("rubric") for i in lost if rel(i)); print("verlorene relevante nach Rubrik:", dict(rub), "Brisanz:", dict(collections.Counter(i["ai"].get("brisanz") for i in lost if rel(i))))
unj = [i for i in items if not i.get("ai")]
print("unbeurteilt", len(unj), "nach Filter", sum(1 for i in unj if pre.search(text(i)) or i.get("trusted")))
groups = {}
for r in cfg["rubrics"]:
    for k in ("must", "core"):
        if r.get(k):
            groups[f'{r["id"]}.{k}'] = re.compile(r[k], re.I)
for k in ("events", "boost", "radar"):
    groups[k] = re.compile(cfg[k], re.I)
groups["kontext"] = re.compile(cfg["ai"]["tariff_context"], re.I)
tg = lambda i: tuple(sorted(g for g, rx in groups.items() if rx.search(text(i))))
rl = [i for i in lost if rel(i)]
print("verloren relevant, Sprachen:", dict(collections.Counter(i["lang"] for i in rl)))
print("verloren relevant, Tags:", [(c, n) for c, n in collections.Counter(tg(i) for i in rl).most_common(8)])
print("verloren relevant, Quellen trusted/open:", sum(bool(i.get("trusted")) for i in rl), sum(bool(i.get("open")) for i in rl), "ohne Land", sum(1 for i in rl if not i.get("countries")))
print("verworfen irrelevant, Sprachen:", dict(collections.Counter(i["lang"] for i in lost if not rel(i))))
