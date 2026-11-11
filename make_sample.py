#!/usr/bin/env python3
"""Erzeugt klar gekennzeichnete BEISPIELDATEN, damit das Design ohne Netzwerk geprüft werden kann.
Wird vom echten Abruf (fetch_news.py / fetch_indices.py) komplett ersetzt."""
import datetime as dt
import json
import math
from pathlib import Path

D = Path(__file__).parent / "data"
now = dt.datetime.now(dt.timezone.utc)

# (Stunden alt, Rubrik, Titel, Originaltitel, Sprache, Länder, Quellen-Anzahl)
S = [
 (3, "haefen", "Beispiel: Terminalbetreiber bestellt weitere Containerbrücken für Kaierweiterung", "Example: Terminal operator orders additional ship-to-shore cranes", "en", ["NL"], 3),
 (9, "haefen", "Beispiel: Hafenausbau am Mittelmeer geht in die nächste Bauphase", "Exemple : l'extension du port entre dans sa phase suivante", "fr", ["MA"], 2),
 (30, "haefen", "Beispiel: Umschlagsvolumen im Containerverkehr steigt im Quartal", "Voorbeeld: containeroverslag stijgt in het kwartaal", "nl", ["BE"], 1),
 (55, "haefen", "Beispiel: Neue RTG-Krane für Terminal am Bosporus angekündigt", "Örnek: yeni RTG vinçleri duyuruldu", "tr", ["TR"], 1),
 (80, "haefen", "Beispiel: Hafen erhält Fördermittel für Elektrifizierung der Kaikrane", "Beispiel: Hafen erhält Fördermittel für Elektrifizierung der Kaikrane", "de", [], 1),
 (5, "kraene", "Beispiel: Kranvermieter erweitert Flotte um Raupenkrane der 750-Tonnen-Klasse", "Example: Crane rental firm adds 750-tonne crawler cranes", "en", [], 2),
 (22, "kraene", "Beispiel: Turmdrehkran-Hersteller meldet Auftragsplus im Bausektor", "Beispiel: Turmdrehkran-Hersteller meldet Auftragsplus im Bausektor", "de", [], 1),
 (49, "kraene", "Beispiel: Mobilkran-Markt: Lieferzeiten verkürzen sich spürbar", "Example: Mobile crane market sees shorter lead times", "en", [], 1),
 (101, "kraene", "Beispiel: Vinç filosunu büyüten şirket yeni siparişleri açıkladı", "Örnek: vinç filosunu büyüten şirket yeni siparişler", "tr", ["TR"], 1),
 (14, "industrie", "Beispiel: Stahlwerk fährt Hochofen nach Wartung wieder an", "Beispiel: Stahlwerk fährt Hochofen nach Wartung wieder an", "de", [], 2),
 (41, "industrie", "Beispiel: Schwerindustrie meldet höhere Investitionen in Prozesskrane", "Exemple : l'industrie lourde investit dans les ponts roulants", "fr", ["DZ"], 1),
 (95, "industrie", "Beispiel: Aciérie : modernisation du parc de levage prévue", "Exemple : modernisation du parc de levage", "fr", ["TN"], 1),
 (27, "tiefbau", "Beispiel: Großprojekt im Spezialtiefbau: Schlitzwand für Tunnelbaustelle", "Beispiel: Großprojekt im Spezialtiefbau: Schlitzwand für Tunnelbaustelle", "de", ["BE"], 2),
 (66, "tiefbau", "Beispiel: Bohrgerätehersteller präsentiert neue Seilbagger-Generation", "Example: Drilling-rig maker presents new cable-excavator generation", "en", [], 1),
 (120, "tiefbau", "Beispiel: Diepwand-project in havenomgeving gegund", "Voorbeeld: diepwandproject in havengebied gegund", "nl", ["NL"], 1),
 (6, "laender", "Beispiel: EU und Türkei verhandeln über Stahl-Einfuhrquoten", "Example: EU and Turkey negotiate steel import quotas", "en", ["TR"], 4),
 (18, "laender", "Beispiel: Marokko senkt Einfuhrzölle auf Industrieausrüstung", "Exemple : le Maroc abaisse les droits de douane sur les équipements", "fr", ["MA"], 2),
 (36, "laender", "Beispiel: Algerien lockert Importregeln für Maschinen", "Exemple : l'Algérie assouplit les règles d'importation", "fr", ["DZ"], 1),
 (52, "laender", "Beispiel: Tunesien: Währung und Konjunktur im Überblick", "Exemple : Tunisie, devise et conjoncture", "fr", ["TN"], 1),
 (60, "laender", "Beispiel: Israel: Hafenlogistik nach Störungen wieder im Normalbetrieb", "Example: Israel port logistics back to normal", "en", ["IL"], 2),
 (75, "laender", "Beispiel: Belgien: Streik im Hafenbetrieb angekündigt", "Voorbeeld: staking in de haven aangekondigd", "nl", ["BE"], 2),
 (88, "laender", "Beispiel: Niederlande: Konjunkturprognose für die Industrie angehoben", "Beispiel: Niederlande: Konjunkturprognose für die Industrie angehoben", "de", ["NL"], 1),
 (4, "rohstoffe", "Beispiel: Stahlwerk kündigt neuen Legierungszuschlag für Walzdraht an", "Beispiel: Stahlwerk kündigt neuen Legierungszuschlag für Walzdraht an", "de", [], 3),
 (20, "rohstoffe", "Beispiel: Zinkpreis zieht an – Verzinkereien rechnen mit Aufschlägen", "Example: Zinc price climbs, galvanizers expect surcharges", "en", [], 2),
 (44, "rohstoffe", "Beispiel: EU berät über Verlängerung der Stahl-Schutzmaßnahmen", "Example: EU weighs extension of steel safeguard", "en", [], 3),
 (70, "rohstoffe", "Beispiel: Schrottpreise geben nach – Marktteilnehmer abwartend", "Beispiel: Schrottpreise geben nach – Marktteilnehmer abwartend", "de", [], 1),
 (11, "markt", "Beispiel: Seilhersteller eröffnet neues Werk für Kranseile", "Example: Rope maker opens new plant for crane ropes", "en", [], 2),
 (58, "markt", "Beispiel: Wire-rope-Markt: Nachfrage nach Hochleistungsseilen wächst", "Example: Wire rope market: demand for high-performance ropes grows", "en", [], 1),
 (110, "markt", "Beispiel: Çelik halat üreticisi ihracatını artırdı", "Örnek: çelik halat üreticisi ihracatını artırdı", "tr", ["TR"], 1),
]

items = []
for k, (h, rub, de, orig, lang, ctry, n) in enumerate(S):
    pub = now - dt.timedelta(hours=h)
    for j in range(n):  # mehrere Quellen = gleicher Titel, damit die Bündelung sichtbar wird
        items.append(dict(id=f"s{k}_{j}", title_orig=orig, title_de=de, lang=lang,
                          source=["Beispielquelle A", "Beispielquelle B", "Beispielquelle C", "Beispielquelle D"][j],
                          url="#", published=(pub - dt.timedelta(minutes=7 * j)).isoformat(),
                          rubric=rub, countries=ctry))
(D / "news.json").write_text(json.dumps(dict(meta=dict(updated=now.isoformat(), sample=True), items=items),
                                        ensure_ascii=False, indent=1), encoding="utf-8")


def month_series(n, end_y, end_m):
    pts = []
    y, m = end_y, end_m
    for i in range(n):
        pts.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    pts.reverse()
    out = []
    for i, (y, m) in enumerate(pts):
        v = 138 + 9 * math.sin(i / 5.0) - 0.18 * i + 0.6 * math.sin(i * 1.7)
        out.append(dict(p=f"{y}-{m:02d}", v=round(v, 1)))
    return out


def quarter_series(n, end_y, end_q):
    pts, y, q = [], end_y, end_q
    for i in range(n):
        pts.append((y, q))
        q -= 1
        if q == 0:
            y, q = y - 1, 4
    pts.reverse()
    return [dict(p=f"{y}-Q{q}", v=round(100 + 1.15 * i + 0.8 * math.sin(i), 1)) for i, (y, q) in enumerate(pts)]


(D / "indices.json").write_text(json.dumps(dict(meta=dict(sample=True), series=dict(
    draht=dict(points=month_series(36, 2026, 9), fetched="Beispiel"),
    aki=dict(points=quarter_series(20, 2026, 2), fetched="Beispiel"))), ensure_ascii=False, indent=1), encoding="utf-8")
print("Beispieldaten geschrieben")
