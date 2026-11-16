#!/usr/bin/env python3
"""Prüft die festen Regeln auf Beispieldaten (ohne Netz, ohne Claude): python test_rules.py"""
import datetime as dt
import os

os.environ["CUSTOMERS"] = "Port Alpha NV Belgien, Beta Steel, Marokko\nGamma | gamma.com.tr"
import ai  # noqa: E402
import build  # noqa: E402
import names  # noqa: E402

UTC = dt.timezone.utc

# NEU = seit gestern 06:30 Berlin, egal ob der Lauf vor oder nach 06:30 startet
for run in ("2026-11-13T04:33", "2026-11-13T11:30"):
    assert build.new_since(dt.datetime.fromisoformat(run).replace(tzinfo=UTC)) == dt.datetime(2026, 11, 12, 5, 30, tzinfo=UTC), run

# Firmenliste: Land am Ende, Land als eigener Eintrag, Website
assert names.parse("CUSTOMERS") == [("Port Alpha", None, "BE"), ("Beta Steel", None, "MA"), ("Gamma", "gamma.com.tr", None)]

# Seite: Links nur http(s)
assert build.safe_url("javascript:alert(1)") == "#" and build.safe_url("https://a.de/x") == "https://a.de/x"


# Auswahl: Kunden umgehen Limit und Mindest-Brisanz und landen nie in „Wettbewerb“; jede Meldung genau einmal
def item(n, rubric, bris, title):
    return dict(id=f"x{n}", title_orig=title, title_de=title, lang="de", source=f"Q{n}", url="https://q.de",
                published=(dt.datetime.now(UTC) - dt.timedelta(hours=n)).isoformat(), rubric=rubric, rubrics=[rubric],
                countries=["BE"], snippet="",
                ai=dict(relevant=True, rubric=rubric, countries=["BE"], brisanz=bris))


items = [item(n, "haefen", 5, f"Terminal {n} Ausbau Kai {chr(65 + n)}") for n in range(8)]
items += [item(20, "haefen", 2, "Port Alpha erweitert Lager"), item(21, "markt", 5, "Port Alpha meldet Großauftrag Hafen")]
_, sections, _ = build.compute(items, dt.datetime.now(UTC))
shown = {s["id"]: [c["id"] for c in s["shown"]] for s in sections}
assert "x20" in shown["haefen"], "Kundenmeldung mit Brisanz 2 fehlt"
assert "x21" not in shown["markt"], "Kunde steht unter Wettbewerb"
flat = [i for ids in shown.values() for i in ids]
assert len(flat) == len(set(flat)), "Meldung doppelt"
assert sum(1 for i in shown["haefen"] if i not in ("x20", "x21")) <= build.SITE["per_section"]

# Dopplungen: Claudes Gruppen (gleiche Titel nur einmal geschickt) werden zu einer Karte; ohne Gruppe eigene Karte
def ev(n, h, title):
    return dict(item(n, "kraene", 5, title), published=(dt.datetime.now(UTC) - dt.timedelta(hours=h)).isoformat(), countries=["MA"],
                ai=dict(relevant=True, rubric="kraene", countries=["MA"], brisanz=5))


evs = [ev(30, 50, "Explosion im Werk Zandor"), ev(31, 30, "Festnahmen bei Protest am Zandor-Werk"), ev(32, 29, "Festnahmen bei Protest am Zandor-Werk"),
       ev(33, 3, "17 Tote bei Explosion in Stahlwerk"), ev(34, 20, "Hafen Tanger: Streik legt Umschlag lahm")]
sent = []


def fake_call(key, system, user, tool, **kw):
    sent.append(user)
    return dict(groups=[["x30", "x31", "x33", "x99"], ["x34"]])


ai.call = fake_call
assert ai.group_stories("k", evs) == 1 and sent[0].count("Festnahmen") == 1
assert {i["id"]: i.get("grp") for i in evs} == dict(x30="gx30", x31="gx30", x32="gx30", x33="gx30", x34=None)
_, sections, _ = build.compute(evs, dt.datetime.now(UTC))
kr = [c for s in sections if s["id"] == "kraene" for c in s["shown"]]
assert sorted(c["n"] for c in kr) == [1, 4], [c["title"] for c in kr]
print("Regeln ok")
