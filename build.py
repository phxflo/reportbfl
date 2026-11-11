#!/usr/bin/env python3
"""Baut docs/index.html aus config.yaml, data/news.json und data/indices.json."""
import datetime as dt
import json
import math
import re
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
def tokens(t):
    return {w for w in re.findall(r"\w+", t.lower()) if len(w) > 3}


def cluster(items):
    """Bündelt gleiche/ähnliche Meldungen verschiedener Quellen zu einer Karte."""
    items = sorted(items, key=lambda i: i["published"], reverse=True)
    groups = []
    for it in items:
        tk = tokens(it.get("title_de") or it["title_orig"])
        for g in groups:
            inter = len(tk & g["tk"])
            if tk and g["tk"] and inter / len(tk | g["tk"]) >= 0.6:
                g["members"].append(it)
                break
        else:
            groups.append(dict(tk=tk, members=[it]))
    return [g["members"] for g in groups]


def main():
    news, idx = load("news.json"), load("indices.json")
    sample = news["meta"].get("sample") or idx["meta"].get("sample")
    now = dt.datetime.now(dt.timezone.utc)
    win = now - dt.timedelta(days=SITE["window_days"])
    rub = {r["id"]: r for r in CFG["rubrics"]}
    cname = {c["id"]: c["name"] for c in CFG["countries"]}

    items = [i for i in news["items"] if dt.datetime.fromisoformat(i["published"]) >= win]
    cards = []
    for members in cluster(items):
        # Lead-Meldung: bevorzugt deutsche/übersetzte, sonst neueste
        lead = members[0]
        pub = dt.datetime.fromisoformat(lead["published"])
        title = lead.get("title_de") or lead["title_orig"]
        text = title + " " + lead["title_orig"]
        srcs = sorted({m["source"] for m in members})
        age = max(0.0, (now - pub).total_seconds() / 86400)
        score = (rub[lead["rubric"]]["weight"] * 2 + 1.6 * (len(srcs) - 1)
                 + (2.5 if BOOST.search(text) else 0) + 2.5 * max(0, 1 - age / SITE["window_days"])
                 + (0.4 if lead["countries"] else 0))
        cards.append(dict(
            rubric=lead["rubric"], rubric_short=rub[lead["rubric"]]["short"], title=title,
            orig=lead["title_orig"] if lead["lang"] != "de" and lead.get("title_de") else None,
            lang=LANG.get(lead["lang"], lead["lang"].upper()), source=srcs[0], n=len(srcs),
            others=", ".join(srcs[1:4]), url=lead["url"],
            when=pub.astimezone(TZ).strftime("%d.%m., %H:%M"), ts=pub, is_new=age < 1,
            countries=[dict(id=c, name=cname[c]) for c in lead["countries"] if c in cname],
            score=score, radar=bool(RADAR.search(text))))

    # Top-News der Woche: höchste Punktzahl, höchstens 2 je Rubrik
    top, per = [], {}
    for c in sorted(cards, key=lambda c: c["score"], reverse=True):
        if per.get(c["rubric"], 0) < 2:
            top.append(c)
            per[c["rubric"]] = per.get(c["rubric"], 0) + 1
        if len(top) == 5:
            break

    sections = []
    for k, r in enumerate(CFG["rubrics"], 1):
        lst = sorted([c for c in cards if c["rubric"] == r["id"]], key=lambda c: c["ts"], reverse=True)
        sections.append(dict(id=r["id"], num=f"{k:02d}", title=r["title"], short=r["short"],
                             shown=lst[:SITE["per_section"]], more=lst[SITE["per_section"]:], total=len(lst)))

    radar_c = []
    for c in CFG["countries"]:
        mine = sorted([x for x in cards if any(cc["id"] == c["id"] for cc in x["countries"])], key=lambda x: x["ts"], reverse=True)
        radar_c.append(dict(id=c["id"], name=c["name"], count=len(mine), latest=mine[0]["title"] if mine else None))

    charts = []
    for spec in CFG["indices"]:
        s = idx["series"].get(spec["id"])
        if s and len(s["points"]) > 4:
            charts.append(chart(spec, s))

    zus = sorted([c for c in cards if c["radar"]], key=lambda c: c["ts"], reverse=True)[:6]
    local = now.astimezone(TZ)
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape())
    env.filters["arrow"] = arrow
    html = env.get_template("index.html.j2").render(
        site=SITE, sample=sample, charts=charts, top=top, sections=sections, radar_c=radar_c, zus=zus,
        countries=CFG["countries"], date=f"{WDAYS[local.weekday()]}, {local.day}. {MONTHS[local.month - 1]} {local.year}",
        updated=local.strftime("%d.%m.%Y, %H:%M Uhr"), edition=local.timetuple().tm_yday,
        n_week=len(cards), n_today=sum(c["is_new"] for c in cards), n_src=len({i["source"] for i in items}),
        errors=idx["meta"].get("errors", []))
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "index.html").write_text(html, encoding="utf-8")
    print(f"docs/index.html: {len(cards)} Meldungen, {len(charts)} Diagramme")


if __name__ == "__main__":
    main()
