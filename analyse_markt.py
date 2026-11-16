"""Einmalige Auswertung (nur Zahlen, keine Inhalte): Wettbewerber- und Kundenmeldungen im Archiv."""
import collections, datetime as dt, difflib, json, re
import build
news = build.load("news.json")
items = news["items"]
now = dt.datetime.now(dt.timezone.utc)
win = [i for i in items if (now - dt.datetime.fromisoformat(i["published"])).days < 8]
print("Meldungen im Fenster:", len(win), "von", len(items))
def kind(i): return i.get("grp") or "offen"
for g in ("wettb", "kunden", "offen"):
    s = [i for i in win if kind(i) == g]
    rel = [i for i in s if (i.get("ai") or {}).get("relevant")]
    rub = collections.Counter((i["ai"] or {}).get("rubric") for i in rel)
    bris = collections.Counter((i["ai"] or {}).get("brisanz") for i in rel)
    print(g, "gesamt", len(s), "relevant", len(rel), "Rubriken", dict(rub), "Brisanz", dict(sorted(bris.items())))
    print("  ohne Urteil:", sum(1 for i in s if not i.get("ai")), "Firmen mit Treffern:", len({i.get("firma") for i in s if i.get("firma") is not None}),
          "Firmen mit relevantem Treffer:", len({i.get("firma") for i in rel if i.get("firma") is not None}))
rel_markt = [i for i in win if (i.get("ai") or {}).get("relevant") and i["ai"].get("rubric") == "markt"]
print("markt relevant:", len(rel_markt), "davon wettb", sum(kind(i) == "wettb" for i in rel_markt), "kunden", sum(kind(i) == "kunden" for i in rel_markt), "offen", sum(kind(i) == "offen" for i in rel_markt))
print("markt Brisanz:", dict(sorted(collections.Counter(i["ai"]["brisanz"] for i in rel_markt).items())))
# Seite wie im Lauf berechnen
build.prepare(news)
cards, top, sections, _ = build.compute(items, now)
for s in sections:
    sh = s["shown"]
    print(s["id"], "angezeigt", len(sh), "Kunde", sum(1 for c in sh if c["kunde"]), "Brisanz", dict(sorted(collections.Counter(c["bris"] for c in sh).items())))
# Doppelte Titel unter allen angezeigten
shown = [(s["id"], c) for s in sections for c in s["shown"]]
norm = lambda t: re.sub(r"\W+", " ", t.lower()).strip()
dups = 0
for a in range(len(shown)):
    for b in range(a + 1, len(shown)):
        if difflib.SequenceMatcher(None, norm(shown[a][1]["title"]), norm(shown[b][1]["title"])).ratio() > 0.8:
            dups += 1
            print("  Dublette zwischen", shown[a][0], "und", shown[b][0])
print("Dublettenpaare:", dups)
