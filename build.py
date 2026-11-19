#!/usr/bin/env python3
"""Baut docs/index.html aus config.yaml, data/news.json und data/indices.json."""
import collections
import datetime as dt
import json
import re
import unicodedata
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
CFG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
SITE = CFG["site"]
TZ = ZoneInfo(SITE["timezone"])
MONTHS = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
WDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
BOOST = re.compile(CFG["boost"], re.I)


def num(v, d=1):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def load(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


# ───────────────────────── Kennzahlen-Diagramme (reines SVG, kein JS) ─────────────────────────
def per_label(p, freq, short=True):
    if freq == "monthly":
        y, m = p.split("-")
        return f"{MONTHS[int(m) - 1]} {y[2:] if short else y}"
    y, q = p.split("-")
    return f"{q} {y[2:] if short else y}"


def chart(spec, series):
    pts = series["points"]
    freq = spec["freq"]
    lag = 12 if freq == "monthly" else 4
    yoy_mode = spec.get("headline") == "yoy"
    if yoy_mode:                            # Inflationsrate = Jahresveränderung des Index (Destatis rechnet ebenso aus dem gerundeten Index)
        pts = [dict(p=pts[i]["p"], v=round((pts[i]["v"] / pts[i - lag]["v"] - 1) * 100, 1)) for i in range(lag, len(pts))]
    dec = 1 if yoy_mode else 0
    W, H, L, R, T, B = 560, 200, 44, 14, 14, 28
    vals = [p["v"] for p in pts]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.12 or 1
    lo, hi = lo - pad, hi + pad
    X = lambda i: L + (W - L - R) * i / (len(pts) - 1)
    Y = lambda v: T + (H - T - B) * (1 - (v - lo) / (hi - lo))
    line = " ".join(f"{'M' if i == 0 else 'L'}{X(i):.1f},{Y(p['v']):.1f}" for i, p in enumerate(pts))
    area = f"{line} L{X(len(pts) - 1):.1f},{H - B} L{X(0):.1f},{H - B} Z"
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{spec["title"]}, Verlauf von {per_label(pts[0]["p"], freq, False)} bis {per_label(pts[-1]["p"], freq, False)}">']
    for k in range(4):
        v = lo + (hi - lo) * k / 3
        y = Y(v)
        s.append(f'<line class="grid" x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}"/><text x="{L - 6}" y="{y + 4:.1f}" text-anchor="end">{num(v, dec)}</text>')
    idx = sorted({0, len(pts) // 4, len(pts) // 2, 3 * len(pts) // 4, len(pts) - 1})
    for i in idx:
        anchor = "start" if i == 0 else "end" if i == len(pts) - 1 else "middle"
        s.append(f'<text x="{X(i):.1f}" y="{H - 8}" text-anchor="{anchor}">{per_label(pts[i]["p"], freq)}</text>')
    s.append(f'<path class="area" d="{area}"/><path class="line" d="{line}"/>')
    for i, p in enumerate(pts):
        s.append(f'<circle class="hit" cx="{X(i):.1f}" cy="{Y(p["v"]):.1f}" r="7"><title>{per_label(p["p"], freq, False)}: {num(p["v"])}</title></circle>')
    s.append(f'<circle class="dot" cx="{X(len(pts) - 1):.1f}" cy="{Y(vals[-1]):.1f}" r="4.5"/></svg>')

    last = pts[-1]["v"]
    prev = pts[-2]["v"]
    yoy = pts[-1 - lag]["v"] if len(pts) > lag else None
    pct = lambda a, b: (a / b - 1) * 100
    if yoy_mode:
        diff = pts[-1]["v"] - pts[-2]["v"]
        return dict(id=spec["id"], title=spec["title"], sub=spec["sub"],
                    url=spec["url"].rsplit("/", 1)[0] + "/" + series.get("table", spec["table"]),
                    latest=num(last) + " %", period=per_label(pts[-1]["p"], freq, False), d1=None, d12=None,
                    note=("▲ +" if diff >= 0 else "▼ −") + num(abs(diff)) + " Prozentpunkte ggü. Vormonat",
                    svg="".join(s), fetched=series.get("fetched", ""))
    return dict(id=spec["id"], title=spec["title"], sub=spec["sub"], url=spec["url"].rsplit("/",1)[0] + "/" + series.get("table", spec["table"]),
                latest=num(last), period=per_label(pts[-1]["p"], freq, False),
                d1=pct(last, prev), d1_label="Vormonat" if freq == "monthly" else "Vorquartal",
                d12=pct(last, yoy) if yoy else None, svg="".join(s), fetched=series.get("fetched", ""))


def arrow(x):
    return ("▲ +" if x >= 0 else "▼ −") + num(abs(x)) + " %"


# ───────────────────────── Meldungen ─────────────────────────
def norm(t):
    """klein, ohne Akzente (İzmir = Izmir, é = e), damit Schreibweisen zusammenpassen"""
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(ch for ch in t if not unicodedata.combining(ch)).replace("ı", "i").replace("ß", "ss")


def tokens(t):
    return {w for w in re.findall(r"\w+", norm(t)) if len(w) > 3}


def similar(a, b):
    if not a or not b:
        return False
    inter = len(a & b)
    small = min(len(a), len(b))
    return inter / len(a | b) >= 0.6 or (small >= 4 and inter / small >= 0.85)


def cluster(items):
    """Bündelt gleiche/ähnliche Meldungen (auch aus anderen Quellen und Sprachen) zu einer Karte."""
    items = sorted(items, key=lambda i: i["published"], reverse=True)
    groups = []
    for it in items:
        tk = tokens((it.get("title_de") or "") + " " + it["title_orig"])
        for g in groups:
            if similar(tk, g["tk"]):
                g["members"].append(it)
                g["tk"] |= tk
                break
        else:
            groups.append(dict(tk=set(tk), members=[it]))
    return [g["members"] for g in groups]



def _ratings():
    f = ROOT / "data" / "ratings.json"
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except ValueError:
        return {}


RATE = _ratings()      # Ampel-Bewertungen des Nutzers {id: {r: g|y|r, t}}
import names
# Kunden im Text erkennen: Kürzel (bis 4 Zeichen) nur in Großschreibung, und wenn ein Kundenland bekannt ist, muss die Meldung auch dieses Land betreffen
CUSTX = [(re.compile(rf"(?<!\w){re.escape(n)}(?!\w)", 0 if len(n) <= 4 else re.I), cid) for n, _, cid in names.parse("CUSTOMERS")]


def cust_hit(text, countries):
    return any(rx.search(text) and (cid is None or cid in countries) for rx, cid in CUSTX)


def country_matchers():
    out = {}
    for c in CFG["countries"]:
        parts = []
        for n in c["names"]:
            e = re.escape(n)
            if not re.match(r"[A-Za-zÀ-ÿİ]", n):       # arabisch/hebräisch: Vorsilben (ب, ב …) erlauben
                parts.append(e)
            elif len(n) <= 4:
                parts.append(rf"(?<!\w){e}(?!\w)")
            else:
                parts.append(rf"(?<!\w){e}")
        out[c["id"]] = re.compile("|".join(parts), re.I)
    return out


CUSTOMER = set((CFG.get("region") or {}).get("rubrics", []))   # Häfen, Krane, Industrie, Spezialtiefbau


def index_notes(idx, now):
    """Kennzahlen-Hinweise: kurz und nur, wenn eine Reihe fehlt oder länger als 7 Tage nicht aktualisiert wurde.
    Ein einzelner fehlgeschlagener Abruf bei Destatis (Reihe noch frisch) ist keinen Hinweis wert."""
    out = []
    for e in idx["meta"].get("errors", []):
        sid = e.split(":")[0]
        ser = (idx.get("series") or {}).get(sid)
        if not ser:
            out.append(f"{sid}: keine Daten")
            continue
        try:
            age = (now.date() - dt.date.fromisoformat(ser["fetched"])).days
        except (KeyError, ValueError):
            age = 99
        if age > 7:
            out.append(f"{sid}: Stand von vor {age} Tagen")
    return out


def safe_url(u):
    return u if u.startswith(("https://", "http://")) else "#"


def show_bericht(b):
    """Bericht für die Seite: nur aktuelle Fassung; Quellen als schlichter Domainname (kurz, einheitlich, nie abgeschnitten)."""
    if not isinstance(b, dict) or b.get("v") != 4:
        return None
    from urllib.parse import urlparse
    return dict(b, quellen=[dict(u=safe_url(q["u"]), t=urlparse(q["u"]).netloc.removeprefix("www.") or q["t"]) for q in b.get("quellen", [])])


def new_since(now):
    """Referenz für „NEU“: gestern 06:30 (Berlin), egal ob der Lauf vor oder nach 06:30 startet."""
    loc = now.astimezone(TZ)
    ref = loc.replace(hour=6, minute=30, second=0, microsecond=0)
    return (ref - dt.timedelta(days=1)).astimezone(dt.timezone.utc)


def compute(all_items, now):
    """Wählt aus: je Rubrik die wichtigsten Meldungen (höchstens per_section)."""
    win = now - dt.timedelta(days=SITE["window_days"])
    fresh = new_since(now)
    rub = {r["id"]: r for r in CFG["rubrics"]}
    rorder = {r["id"]: k for k, r in enumerate(CFG["rubrics"])}
    cname = {c["id"]: c["name"] for c in CFG["countries"]}
    cmatch = country_matchers()
    cap = SITE["per_section"]

    allowed = set(CFG["editions"]) | {"de", "en"}
    judged = any(i.get("ai") for i in all_items)          # ohne jedes Urteil (Vorschau/kein Schlüssel) zeigen wir alles; sonst nur, was Claude für relevant hält
    items = [i for i in all_items if dt.datetime.fromisoformat(i["published"]) >= win and (i["lang"] in allowed or i["id"].startswith("s")) and (i.get("ai") or {}).get("relevant", not judged)]
    cards = []
    for members in cluster(items):
        lead = members[0]
        rubrics = sorted({r for m in members for r in (m.get("rubrics") or [m["rubric"]])}, key=lambda r: rorder.get(r, 99))
        ai = [m["ai"] for m in members if m.get("ai")]
        if ai:                                   # Claude hat entschieden: Rubrik(en) und Länder kommen von dort
            rubrics = sorted({a["rubric"] for a in ai if a.get("rubric")}, key=lambda r: rorder.get(r, 99)) or rubrics
        rubrics = [r for r in rubrics if r in rorder]
        if not rubrics:
            continue
        rubric = rubrics[0]
        # Land = Land, um das es inhaltlich geht: Namen in Titel/Textauszug oder Land in der Suche selbst – nicht das Quellland
        text_all = " ".join((m.get("title_de") or "") + " " + m["title_orig"] + " " + m.get("snippet", "") for m in members)
        countries = sorted({c for c in cname if cmatch[c].search(text_all)}, key=list(cname).index)
        if ai:
            countries = sorted({c for a in ai for c in a.get("countries", []) if c in cname}, key=list(cname).index)
        # regionale Eingrenzung: Zielmärkte nur mit Bezug zu deinen Ländern
        reg = CFG.get("region") or {}
        if reg:
            if not ai and any(m["lang"] == "tr" for m in members) and "TR" in cname and "TR" not in countries:
                countries = sorted(countries + ["TR"], key=list(cname).index)
            rubrics = [r for r in rubrics if r not in reg.get("rubrics", []) or countries]
            if not rubrics:
                continue
            rubric = rubrics[0]
        if rubrics == ["laender"] and not countries and not ai:      # Zölle/Tarife dürfen auch ohne Land stehen (EU-/Weltmarkt), wenn Claude sie so einordnet
            continue
        pub = dt.datetime.fromisoformat(lead["published"])
        title = next((m["title_de"] for m in members if m.get("title_de")), lead["title_orig"])
        text = title + " " + lead["title_orig"]
        srcs = sorted({m["source"] for m in members})
        cards.append(dict(
            id=lead["id"], bericht=show_bericht(lead.get("bericht")), trusted=any(m.get("trusted") for m in members), srcs=set(srcs),
            rubric=rubric, rubrics=rubrics, title=title, lead=lead, text=text,
            orig=lead["title_orig"] if lead["lang"] != "de" and title != lead["title_orig"] else None,
            source=srcs[0], n=len(srcs), url=safe_url(lead["url"]),
            when=pub.astimezone(TZ).strftime("%d.%m. %H:%M"), ts=pub, is_new=pub >= fresh,
            countries=[dict(id=c, name=cname[c]) for c in countries], grp={m["grp"] for m in members if m.get("grp")},
            bris=max([m["ai"]["brisanz"] for m in members if m.get("ai")] or [0]),
            kunde=any(m.get("kunde") for m in members) or cust_hit(title + " " + lead["title_orig"] + " " + (lead.get("snippet") or ""), countries), ai_used=bool(ai), rc=collections.Counter(a["rubric"] for a in ai if a.get("rubric")) or collections.Counter([rubric]),
            readable=lead["lang"] in ("de", "en") or any(m.get("title_de") for m in members)))

    # Gleiche Vorfälle (auch in anderen Sprachen, z. B. die Explosion in Izmir) zu einer Meldung bündeln.
    # Als Hauptmeldung dient die lesbarste: Fachmedium, dann deutsch/übersetzt, dann neueste.
    cards.sort(key=lambda c: (c["trusted"], c["readable"], c["ts"]), reverse=True)
    merged = []
    for c in cards:
        for m in merged:
            if c["grp"] & m["grp"]:                 # dieselbe Geschichte (Claude, ai.group_stories)
                m["grp"] |= c["grp"]
                m["rc"] = m["rc"] + c["rc"]
                m["ai_used"] |= c["ai_used"]
                m["bris"] = max(m["bris"], c["bris"])
                m["srcs"] |= c["srcs"]
                m["rubrics"] = sorted(set(m["rubrics"]) | set(c["rubrics"]), key=lambda r: rorder.get(r, 99))
                have = {k["id"] for k in m["countries"]}
                m["countries"] += [k for k in c["countries"] if k["id"] not in have]
                m["trusted"] |= c["trusted"]
                m["is_new"] |= c["is_new"]
                if c["ts"] > m["ts"]:
                    m["ts"], m["when"] = c["ts"], c["when"]
                break
        else:
            merged.append(c)
    cards = [c for c in merged if RATE.get(c["id"], {}).get("r") != "r"]      # rot bewertet = dauerhaft ausgeblendet
    for c in cards:
        c["rate"] = RATE.get(c["id"], {}).get("r")
        if c["ai_used"]:                    # Claude hat zugeordnet: genau eine Rubrik – die, die die meisten Meldungen des Vorfalls bekamen
            c["rubric"] = max(c["rc"], key=lambda r: (c["rc"][r], -rorder.get(r, 99)))
            c["rubrics"] = [c["rubric"]]
        else:
            c["rubric"] = c["rubrics"][0]
        if c["kunde"] and c["rubric"] == "markt":          # Kunden sind keine Wettbewerber: in den Zielmarkt, der am besten passt
            hits = {r["id"]: len(re.findall(r.get("core") or r["must"], c["title"] + " " + c["lead"]["title_orig"] + " " + (c["lead"].get("snippet") or ""), re.I))
                    for r in CFG["rubrics"] if r.get("tile") and (r.get("core") or r.get("must"))}
            c["rubric"] = max(hits, key=lambda k: (hits[k], k == "industrie")) if hits else c["rubric"]
            c["rubrics"] = [c["rubric"]]
        c["n"] = len(c["srcs"])
        age = max(0.0, (now - c["ts"]).total_seconds() / 86400)
        # Brisanz: Gewicht der Rubrik, Zahl der Quellen, Reizwörter (Zuschlag, Zoll …); Aktualität zählt kaum,
        # damit die Rangfolge über die Woche stabil bleiben
        c["score"] = (rub[c["rubric"]]["weight"] * 2 + 1.2 * min(c["n"] - 1, 8) + (2.5 if BOOST.search(c["text"]) else 0)
                      + 0.8 * max(0, 1 - age / SITE["window_days"]) + (0.4 if c["countries"] else 0)
                      + (1.5 if c["trusted"] else 0) + (1.5 * (c["bris"] - 3) if c["bris"] else 0)
                      + (2.0 if c["rubric"] in CUSTOMER and c["countries"] else 0)
                      + (3.0 if c["kunde"] else 0))      # Kundennähe: Ereignisse bei Kunden in deinen Ländern zuerst

    # Je Rubrik die wichtigsten Meldungen (nach Wertung, nicht nach Datum); Randthemen (niedrige Brisanz) fallen weg
    def member(c, rid):
        if c["rubric"] != rid:
            return False
        if c["ai_used"] and 0 < c["bris"] < rub[rid].get("min_bris", 4) and not c["kunde"]:      # Kundenmeldungen immer
            return False
        if rid == "laender":            # "Länder" = allgemeine Meldungen zum Land
            return c["ai_used"] or bool(c["countries"])
        return True

    picks = {}
    for r in CFG["rubrics"]:
        lst = sorted([c for c in cards if member(c, r["id"])], key=lambda c: (c["score"], c["ts"]), reverse=True)
        cust = [c for c in lst if c["kunde"]]                       # alles zu deinen Kunden bleibt drin, auch über dem Limit
        rest = [c for c in lst if not c["kunde"]][:max(r.get("max", cap) - len(cust), 0)]
        picks[r["id"]] = cust + rest

    sections = []
    for r in CFG["rubrics"]:
        lst = sorted(picks[r["id"]], key=lambda c: (c["score"], c["ts"]), reverse=True)
        sections.append(dict(id=r["id"], group=r.get("group"), tile=bool(r.get("tile")), short=r["short"], shown=lst, limit=r.get("max", cap)))

    return cards, sections, items


def health(news, idx, now, cards=(), shown=()):
    """Systemstatus: Zeilen (Name, Stufe ok/warn/bad, Text). Macht stille Ausfälle sichtbar."""
    rows, meta = [], news["meta"]
    h = meta.get("health")
    if h and h.get("queries"):
        q, ok = h["queries"], h["ok"]
        share = ok / q
        dead = [l for l, (o, n) in (h.get("langs") or {}).items() if n and o == 0]
        txt = f"{ok} von {q} Suchanfragen lieferten Treffer"
        if dead:
            txt += "; ohne jeden Treffer: " + ", ".join(sorted(dead))
        rows.append(("Suche", "ok" if share >= .85 and not dead else "warn" if share >= .6 else "bad", txt))
    for key, label in (("kunden", "Kunden"), ("wettb", "Wettbewerber")):
        f = (h or {}).get("firms", {}).get(key)
        if f and f[1]:
            mark = sum(1 for c in cards if c["kunde"]) if key == "kunden" else None
            rows.append((label, "ok" if f[0] else "warn", f"{f[0]} von {f[1]} Firmen mit Treffern in der Suche" + (f"; {mark} Meldungen markiert" if mark is not None else "")))
    a = meta.get("ai")
    if a:
        if a["status"] == "ok":
            left = max(a.get("todo", 0) - a.get("judged", 0), 0)
            rows.append(("Claude", "ok" if not left else "warn",
                         f"{a.get('judged', 0)} Meldungen beurteilt" + (f", {a['pre']} vorgefiltert" if a.get("pre") else "") + f", {a.get('groups', 0)} Geschichten mit Dopplungen"
                         + (f"; {left} warten auf den nächsten Lauf (Limit {CFG.get('ai', {}).get('max_items', 150)} je Lauf, Kunden zuerst)" if left else "")
                         + (f" · {round(a['tin'] / 1000)}k Token ein, {round(a['tout'] / 1000)}k aus" if a.get("tin") else "")))
        elif a["status"] == "aus":
            rows.append(("Claude", "bad", "Schlüssel fehlt – Meldungen werden nur per Stichwort gefiltert"))
        else:
            rows.append(("Claude", "bad", "Auswertung abgebrochen – es gilt der Stand des Vortags. " + (a.get("error") or "")))
    rs = meta.get("research")
    if rs:
        gone = sum(1 for c in shown if not c["bericht"] and c["lead"].get("bericht") is False and c["lead"].get("bericht_try", 1) >= 3)
        wait = sum(1 for c in shown if not c["bericht"]) - gone
        rows.append(("Recherche", "warn" if rs.get("fails") or wait else "ok",
                     f"{rs.get('n', 0)} neue Berichte, {rs.get('searches', 0)} Suchen" + (f"; {rs['fails']} Fehler" if rs.get("fails") else "")
                     + (f"; {wait} von {len(shown)} angezeigten Meldungen noch ohne Hintergrund (folgt im nächsten Lauf)" if wait else "")
                     + (f"; {gone} ohne auffindbare Quellen" if gone else "")
                     + (f" · {round(rs['tin'] / 1000)}k Token ein, {round(rs['tout'] / 1000)}k aus" if rs.get("tin") else "")))
    if not meta.get("sample"):
        win = now - dt.timedelta(days=SITE["window_days"])
        recent = [i for i in news["items"] if dt.datetime.fromisoformat(i["published"]) >= win]
        if recent:
            age = (now - max(dt.datetime.fromisoformat(i["published"]) for i in recent)).total_seconds() / 3600
            rows.append(("Frische", "ok" if age < 36 else "warn" if age < 72 else "bad", f"neueste Meldung vor {age:.0f} Std."))
    if RATE:
        since = (now - dt.timedelta(days=7)).timestamp() * 1000
        recent_r = {k: v for k, v in RATE.items() if v.get("t", 0) >= since}
        if recent_r:
            by = {i["id"]: i for i in news["items"]}
            tot = collections.Counter(v["r"] for v in recent_r.values())
            n = sum(tot.values())
            share = tot["g"] / n
            per = collections.defaultdict(lambda: [0, 0])
            for k, v in recent_r.items():
                i = by.get(k)
                if i:
                    rb = (i.get("ai") or {}).get("rubric") or i.get("rubric")
                    per[rb][1] += 1
                    per[rb][0] += v["r"] == "g"
            worst = min(((g / n2, rb) for rb, (g, n2) in per.items() if n2 >= 5), default=None)
            txt = f"{n} Bewertungen in 7 Tagen: {round(100 * share)} % grün, {round(100 * tot['y'] / n)} % gelb, {round(100 * tot['r'] / n)} % rot"
            if worst:
                nm = next((r["short"] for r in CFG["rubrics"] if r["id"] == worst[1]), worst[1])
                txt += f"; schwächste Rubrik: {nm} ({round(100 * worst[0])} % grün)"
            rows.append(("Qualität", "ok" if share >= .5 else "warn", txt))   # nur Hinweis, nie „Störung“
    else:
        rows.append(("Qualität", "ok", "noch keine Bewertungen"))
    parts = [f"{sid} {s['points'][-1]['p']}" for sid, s in (idx.get("series") or {}).items() if s.get("points")]
    errs = index_notes(idx, now)
    rows.append(("Kennzahlen", "bad" if errs else "ok",
                 ("; ".join(errs)) if errs else "Stand " + ", ".join(parts)))
    return rows


LATIN = "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"
LATIN_EXT = "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF"


def font_css():
    """Inter (variabel, mit optischen Größen; OFL, fonts/OFL-Inter.txt) direkt einbetten: kein Abruf von außen.
    Auf Apple-Geräten nimmt die Seite die Systemschrift SF Pro, Inter ist der Ersatz für Windows und Android."""
    import base64
    out = []
    for sub, rng in (("latin", LATIN), ("latin-ext", LATIN_EXT)):
        b64 = base64.b64encode((ROOT / "fonts" / f"inter-{sub}-opsz-normal.woff2").read_bytes()).decode()
        out.append(f"@font-face{{font-family:'Inter';font-weight:100 900;font-style:normal;font-display:swap;"
                   f"src:url(data:font/woff2;base64,{b64}) format('woff2');unicode-range:{rng}}}")
    return "".join(out)


def main():
    news, idx = load("news.json"), load("indices.json")
    sample = news["meta"].get("sample") or idx["meta"].get("sample")
    now = dt.datetime.now(dt.timezone.utc)
    rub_items = news["items"]

    cards, sections, items = compute(rub_items, now)
    dist = collections.Counter(c["bris"] for c in cards if c["ai_used"])
    shown = collections.Counter(c["bris"] for s_ in sections for c in s_["shown"])
    print(f"Brisanz der Karten {dict(sorted(dist.items()))}; angezeigt {dict(sorted(shown.items()))}")


    charts = []
    for spec in CFG["indices"]:
        s = idx["series"].get(spec["id"])
        if s and len(s["points"]) > 4:
            charts.append(chart(spec, s))

    local = now.astimezone(TZ)
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=True)
    env.filters["arrow"] = arrow
    html = env.get_template("index.html.j2").render(
        site=SITE, sample=sample, charts=charts, sections=sections,
        countries=CFG["countries"], date=f"{WDAYS[local.weekday()]}, {local.day}. {MONTHS[local.month - 1]} {local.year}",
        updated=local.strftime("%d.%m.%Y, %H:%M Uhr"), edition=local.timetuple().tm_yday,
        errors=index_notes(idx, now), health=health(news, idx, now, cards, [c for s in sections for c in s["shown"]]),
        fontcss=font_css(), rating=SITE.get("rating"))
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "index.html").write_text(html, encoding="utf-8")
    print(f"docs/index.html: {len(cards)} Meldungen im Fenster, {len(charts)} Diagramme")


if __name__ == "__main__":
    main()
