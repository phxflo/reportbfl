#!/usr/bin/env python3
"""Baut docs/index.html aus config.yaml, data/news.json und data/indices.json."""
import datetime as dt
import json
import math
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
CFG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
SITE = CFG["site"]
TZ = ZoneInfo(SITE["timezone"])
MONTHS = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
WDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
LANG = {"de": "DE", "en": "EN", "fr": "FR", "nl": "NL", "tr": "TR", "ar": "AR", "he": "HE"}
BOOST = re.compile(CFG["boost"], re.I)
RADAR = re.compile(CFG["radar"], re.I)


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
        s.append(f'<line class="grid" x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}"/><text x="{L - 6}" y="{y + 4:.1f}" text-anchor="end">{num(v, 0)}</text>')
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
    return dict(id=spec["id"], title=spec["title"], sub=spec["sub"], url=spec["url"],
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


def compute(all_items, now):
    """Wählt aus: Top-News (nach Brisanz) und je Rubrik die neuesten Meldungen (höchstens per_section)."""
    win = now - dt.timedelta(days=SITE["window_days"])
    rub = {r["id"]: r for r in CFG["rubrics"]}
    rorder = {r["id"]: k for k, r in enumerate(CFG["rubrics"])}
    cname = {c["id"]: c["name"] for c in CFG["countries"]}
    cmatch = country_matchers()
    cap = SITE["per_section"]

    allowed = set(CFG["editions"]) | {"de", "en"}
    items = [i for i in all_items if dt.datetime.fromisoformat(i["published"]) >= win and (i["lang"] in allowed or i["id"].startswith("s"))]
    cards = []
    for members in cluster(items):
        lead = members[0]
        rubrics = sorted({r for m in members for r in (m.get("rubrics") or [m["rubric"]])}, key=lambda r: rorder.get(r, 99))
        rubric = rubrics[0]
        # Land = Land, um das es inhaltlich geht: Namen in Titel/Textauszug oder Land in der Suche selbst – nicht das Quellland
        text_all = " ".join((m.get("title_de") or "") + " " + m["title_orig"] + " " + m.get("snippet", "") for m in members)
        countries = sorted({c for c in cname if cmatch[c].search(text_all)}
                           | {c for m in members for c in m.get("countries", []) if c in cname}, key=list(cname).index)
        if rubrics == ["laender"] and not countries:
            continue
        pub = dt.datetime.fromisoformat(lead["published"])
        title = next((m["title_de"] for m in members if m.get("title_de")), lead["title_orig"])
        text = title + " " + lead["title_orig"]
        srcs = sorted({m["source"] for m in members})
        age = max(0.0, (now - pub).total_seconds() / 86400)
        # Brisanz: Gewicht der Rubrik, Zahl der Quellen, Reizwörter (Zuschlag, Zoll …); Aktualität zählt kaum,
        # damit die Top-News über die Woche stabil bleiben
        score = (rub[rubric]["weight"] * 2 + 1.6 * min(len(srcs) - 1, 3) + (2.5 if BOOST.search(text) else 0)
                 + 0.8 * max(0, 1 - age / SITE["window_days"]) + (0.4 if countries else 0)
                 + (1.5 if any(m.get("trusted") for m in members) else 0))
        cards.append(dict(
            id=lead["id"], trusted=any(m.get("trusted") for m in members),
            rubric=rubric, rubrics=rubrics, rubric_short=rub[rubric]["short"], title=title, lead=lead,
            orig=lead["title_orig"] if lead["lang"] != "de" and title != lead["title_orig"] else None,
            translated=any(m.get("title_de") for m in members) or lead["lang"] in ("de", "en"),
            needs_tr=not (any(m.get("title_de") for m in members) or lead["lang"] in ("de", "en")),
            lang=LANG.get(lead["lang"], lead["lang"].upper()), source=srcs[0], n=len(srcs), url=lead["url"],
            when=pub.astimezone(TZ).strftime("%d.%m. %H:%M"), ts=pub, is_new=age < 1,
            countries=[dict(id=c, name=cname[c]) for c in countries], score=score,
            tk=tokens(title + " " + lead["title_orig"])))

    # Top-News: nach Brisanz; höchstens eine Meldung je Rubrik und je Vorfall. Gleicher Vorfall = innerhalb von
    # 48 Stunden gemeinsamer Eigenname/seltenes Wort (z. B. "Izmir"), auch sprachübergreifend, oder ähnliche Titel.
    # Zwei verschiedene Themen aus demselben Land dürfen dagegen beide erscheinen.
    GENERIC = {"hafen", "haefen", "stahl", "stahlwerk", "kran", "krane", "kranen", "crane", "cranes", "port", "ports", "steel",
               "container", "terminal", "terminals", "industrie", "markt", "market", "zoll", "tariff", "tariffs", "neue", "neuen",
               "wegen", "nach", "durch", "ueber", "ihre", "sind", "wurde", "turkey", "tuerkei", "turkiye", "israel", "marokko",
               "morocco", "maroc", "algerien", "algerie", "tunesien", "tunisie", "belgien", "belgique", "niederlande", "nederland"}
    df = Counter(w for c in cards for w in c["tk"])

    def same_incident(a, b):
        if abs((a["ts"] - b["ts"]).total_seconds()) > 48 * 3600:
            return False
        shared = a["tk"] & b["tk"]
        if len(shared) >= 3:
            return True
        return any(len(w) >= 5 and w not in GENERIC and df[w] <= 25 for w in shared)

    top, used_r = [], set()
    for c in sorted(cards, key=lambda c: (c["score"], c["ts"]), reverse=True):
        if len(top) >= SITE.get("top_n", 5):
            break
        if c["rubric"] in used_r or any(same_incident(c, t) for t in top):
            continue
        top.append(c)
        used_r.add(c["rubric"])

    def member(c, rid):                 # Rubrik "Länder" = alles mit erkennbarem Länderbezug
        return bool(c["countries"]) if rid == "laender" else rid in c["rubrics"]

    sections = []
    for k, r in enumerate(CFG["rubrics"], 1):
        lst = sorted([c for c in cards if member(c, r["id"])], key=lambda c: c["ts"], reverse=True)
        if r["id"] == "laender":        # je Land die neuesten 10, damit der Länderfilter genug Auswahl hat
            pool, seen = [], set()
            for c in cname:
                for x in [x for x in lst if any(cc["id"] == c for cc in x["countries"])][:cap]:
                    if id(x) not in seen:
                        seen.add(id(x))
                        pool.append(x)
            pool.sort(key=lambda c: c["ts"], reverse=True)
            sections.append(dict(id=r["id"], num=f"{k:02d}", title=r["title"], short=r["short"], shown=pool, limit=cap))
        else:
            sections.append(dict(id=r["id"], num=f"{k:02d}", title=r["title"], short=r["short"], shown=lst[:cap], limit=cap))

    return cards, top, sections, items


def main():
    news, idx = load("news.json"), load("indices.json")
    sample = news["meta"].get("sample") or idx["meta"].get("sample")
    now = dt.datetime.now(dt.timezone.utc)
    rub_items = news["items"]

    cards, top, sections, items = compute(rub_items, now)

    # Nur was auf der Seite steht wird übersetzt (Titel), danach neu auswählen: gebündelt über Sprachen hinweg
    if not news["meta"].get("sample") and "--no-translate" not in sys.argv:
        for _ in range(2):
            visible = {id(c["lead"]): c for c in top + [x for s in sections for x in s["shown"]] if not c["translated"]}
            need = [c["lead"] for c in visible.values()][: SITE.get("translate_max", 150)]
            if not need:
                break
            try:
                import translate
                done = translate.translate_titles(need)
            except Exception as ex:
                print("Übersetzung übersprungen:", ex, file=sys.stderr)
                break
            print(f"{done} von {len(need)} Titeln übersetzt")
            if not done:
                break
            (ROOT / "data" / "news.json").write_text(json.dumps(news, ensure_ascii=False, indent=1), encoding="utf-8")
            cards, top, sections, items = compute(rub_items, now)

    charts = []
    for spec in CFG["indices"]:
        s = idx["series"].get(spec["id"])
        if s and len(s["points"]) > 4:
            charts.append(chart(spec, s))

    local = now.astimezone(TZ)
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape())
    env.filters["arrow"] = arrow
    html = env.get_template("index.html.j2").render(
        site=SITE, sample=sample, charts=charts, top=top, sections=sections,
        countries=CFG["countries"], date=f"{WDAYS[local.weekday()]}, {local.day}. {MONTHS[local.month - 1]} {local.year}",
        updated=local.strftime("%d.%m.%Y, %H:%M Uhr"), edition=local.timetuple().tm_yday,
        n_week=len(cards), n_today=sum(c["is_new"] for c in cards), n_src=len({i["source"] for i in items}),
        errors=idx["meta"].get("errors", []))
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "index.html").write_text(html, encoding="utf-8")
    print(f"docs/index.html: {len(cards)} Meldungen im Fenster, {len(charts)} Diagramme")


if __name__ == "__main__":
    main()
