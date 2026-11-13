#!/usr/bin/env python3
"""Holt Meldungen per Google-News-RSS (alle Sprachen), ordnet sie Rubriken/Ländern zu,
übersetzt Titel ins Deutsche und pflegt das Archiv data/news.json."""
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import feedparser
import requests
import yaml

import names

ROOT = Path(__file__).parent
CFG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
NEWS = ROOT / "data" / "news.json"
UA = {"User-Agent": "Mozilla/5.0 (compatible; SeilReport/1.0)"}
HAVE_AI = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())   # nur dann lassen wir weite Suchen ungefiltert durch



def chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def quote_term(t):
    t = str(t)
    return f'"{t}"' if " " in t else t


def feed_url(q, hl, gl, ceid, days):
    q = f"{q} when:{days}d"
    return ("https://news.google.com/rss/search?q=" + urllib.parse.quote(q)
            + f"&hl={hl}&gl={gl}&ceid={urllib.parse.quote(ceid)}")


def competitors():
    return names.parse("COMPETITORS")


def customers():
    return names.parse("CUSTOMERS")


def discover_feeds(domain):
    """Sucht auf der Startseite nach RSS/Atom-Feeds (News-Bereich der Firma). Fehler sind unkritisch."""
    try:
        r = requests.get("https://" + domain, headers=UA, timeout=8)
        links = re.findall(r'<link[^>]+type=["\']application/(?:rss|atom)\+xml["\'][^>]*>', r.text, re.I)
        urls = []
        for l in links:
            m = re.search(r'href=["\']([^"\']+)["\']', l, re.I)
            if m:
                urls.append(urllib.parse.urljoin(r.url, html.unescape(m.group(1))))
        return urls[:2]
    except Exception:
        return []


def company_jobs(entries, days, kunde):
    """Je Firma: Namenssuche in den Ausgaben des Landes (Landessprache, Deutsch, Englisch); bei bekannter Website
    zusätzlich Seiten-Suche (site:) und deren RSS-Feeds."""
    grp = "kunden" if kunde else "wettb"
    jobs = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        feeds = list(pool.map(lambda e: discover_feeds(e[1]) if e[1] else [], entries))
    ctry = {c["id"]: c for c in CFG["countries"]}
    for idx, ((name, dom, cid), fl) in enumerate(zip(entries, feeds)):
        eds = [("de", "de", "DE", "DE:de"), ("en", "en-US", "US", "US:en")]
        for e in (ctry.get(cid) or {}).get("editions", []):
            if e["lang"] not in ("de", "en"):
                eds.append((e["lang"], e["hl"], e["gl"], e["ceid"]))
        for lang, hl, gl, ceid in eds:
            jobs.append(dict(url=feed_url(quote_term(name), hl, gl, ceid, days), rubric="markt", lang=lang,
                             country=cid, open=True, grp=grp, firma=idx))
            if dom and lang in ("de", "en"):
                jobs.append(dict(url=feed_url(f"site:{dom}", hl, gl, ceid, days), rubric="markt", lang=lang,
                                 country=cid, open=True, trusted=True, kunde=kunde, source=name, grp=grp, firma=idx))
        for u in fl:
            jobs.append(dict(url=u, rubric="markt", lang="en", country=cid, open=True, trusted=True, kunde=kunde,
                             source=name, grp=grp, firma=idx))
    return jobs


def build_jobs(days):
    jobs = []
    for r in CFG["rubrics"]:
        for lang, terms in (r.get("terms") or {}).items():
            for ed in CFG["editions"].get(lang, []):
                for grp in chunks(terms, 7):
                    q = "(" + " OR ".join(quote_term(t) for t in grp) + ")"
                    jobs.append(dict(url=feed_url(q, ed["hl"], ed["gl"], ed["ceid"], days),
                                     rubric=r["id"], lang=lang, country=None))
    for c in CFG["countries"]:
        for e in c["editions"]:
            named = any(n.lower() in e["q"].lower() for n in c["names"])
            jobs.append(dict(url=feed_url(e["q"], e["hl"], e["gl"], e["ceid"], days),
                             rubric="laender", lang=e["lang"], country=c["id"] if named else None))
    # Zusatzsuche je Land und Sprache nach Hafen/Kran/Stahl/Bau (nur sinnvoll mit Claude-Auswertung → "open")
    seen = {j["url"] for j in jobs}
    terms = CFG.get("industry_terms") or {}
    for c in CFG["countries"]:
        for e in c["editions"]:
            name = e["q"].split(" (")[0]
            if e["lang"] not in terms or any(w in e["q"].lower() for w in ("crane", "kran", "grue", "kraan", "vinç")):
                continue
            url = feed_url(f"{name} (" + " OR ".join(terms[e["lang"]]) + ")", e["hl"], e["gl"], e["ceid"], days)
            if url not in seen:
                seen.add(url)
                jobs.append(dict(url=url, rubric="laender", lang=e["lang"], country=c["id"], open=True))
    # Wettbewerber und Kunden (Namen/Websites nur als GitHub-Secrets, nie im Repo)
    jobs += company_jobs(competitors()[:30], days, False)
    jobs += company_jobs(customers()[:40], days, True)
    for t in CFG.get("trade_sources") or []:
        q = f"site:{t['site']} {t['q']}"
        jobs.append(dict(url=feed_url(q, "de" if t["lang"] == "de" else "en", "DE" if t["lang"] == "de" else "US",
                                      "DE:de" if t["lang"] == "de" else "US:en", CFG["site"]["fetch_days"]),
                         rubric=t["rubric"], lang=t["lang"], country=None, trusted=True))
    for f in CFG.get("feeds") or []:
        jobs.append(dict(url=f["url"], rubric=f["rubric"], lang=f.get("lang", "de"),
                         country=None, source=f["name"]))
    return jobs


def norm(t):
    t = re.sub(r"\s+", " ", t.lower()).strip()
    return re.sub(r"[^\w ]", "", t)


def fetch(url, tries=3):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=25)
            if r.status_code == 200:
                return feedparser.parse(r.content)
            print(f"  HTTP {r.status_code}", file=sys.stderr)
        except requests.RequestException as e:
            print(f"  Fehler: {type(e).__name__}", file=sys.stderr)
        time.sleep(2 * (i + 1))
    return None



def main():
    days = CFG["site"]["fetch_days"]
    keep = CFG["site"]["retention_days"]
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=keep)
    excl = [e.lower() for e in CFG.get("exclude", [])]
    order = {r["id"]: i for i, r in enumerate(CFG["rubrics"])}
    must = {r["id"]: re.compile(r["must"], re.I) for r in CFG["rubrics"] if r.get("must")}
    core = {r["id"]: re.compile(r["core"], re.I) for r in CFG["rubrics"] if r.get("core")}
    events = re.compile(CFG["events"], re.I) if CFG.get("events") else None
    dropped = {}
    xrx = [re.compile(x, re.I | re.S) for x in CFG.get("exclude_regex", [])]

    def bad(title, src, snip=""):
        low = f"{title} {src}".lower()
        return any(x in low for x in excl) or any(r.search(f"{title} {src} {snip}") for r in xrx)

    def passes(rubric, title, snip, trusted=False):
        """Rubrik-Prüfung: Pflichtwort, danach Kernbegriff oder Ereigniswort (Fachmedien immer)."""
        txt = f"{title} {snip}"
        rx = must.get(rubric)
        if rx and not rx.search(txt):
            return False
        cr = core.get(rubric)
        return not cr or bool(trusted or cr.search(txt) or (events and events.search(title)))

    db = {}
    if NEWS.exists():
        old = json.loads(NEWS.read_text(encoding="utf-8"))
        if not old.get("meta", {}).get("sample"):
            allowed = set(CFG["editions"]) | {"de", "en"}      # Sprachen, die wir suchen; alles andere fliegt aus dem Archiv
            for i in old.get("items", []):
                # Archiv mit den aktuellen Regeln neu prüfen: Ausschlüsse, Sprache, Rubrik-Gating
                if i["lang"] not in allowed or bad(i["title_orig"], i["source"], i.get("snippet", "")):
                    continue
                ok = [r for r in (i.get("rubrics") or [i["rubric"]])
                      if (i.get("open") and HAVE_AI) or passes(r, i["title_orig"], i.get("snippet", ""), i.get("trusted"))]
                if not ok:
                    dropped["Archiv"] = dropped.get("Archiv", 0) + 1
                    continue
                i["rubrics"] = ok
                i["rubric"] = min(ok, key=lambda r: order.get(r, 99))
                db[i["id"]] = i

    jobs = build_jobs(days)
    print(f"{len(jobs)} Abfragen …")
    ok = 0
    def _get(job):
        feed = fetch(job["url"])
        time.sleep(0.5)                        # kleine Pause je Abruf, damit Google nicht drosselt
        return feed

    with ThreadPoolExecutor(max_workers=int(os.environ.get("FETCH_WORKERS", "3"))) as pool:   # mehrere Abfragen gleichzeitig
        feeds = list(pool.map(_get, jobs))
    langs, firms, base = {}, {}, [0, 0]
    for job, feed in zip(jobs, feeds):
        if job.get("grp"):                      # Firmensuchen getrennt zählen: leer ist dort normal
            F = firms.setdefault(job["grp"], [set(), set()])
            F[1].add(job["firma"])
            if feed and feed.entries:
                F[0].add(job["firma"])
        else:
            L = langs.setdefault(job["lang"], [0, 0])
            L[1] += 1
            base[1] += 1
            if feed and feed.entries:
                L[0] += 1
                base[0] += 1
        if not feed or not feed.entries:
            continue
        ok += 1
        for e in feed.entries:
            raw = e.get("title", "").strip()
            src = (e.get("source") or {}).get("title") or job.get("source") or ""
            title = raw[: -len(src) - 3] if src and raw.endswith(f" - {src}") else raw
            if not title or not getattr(e, "published_parsed", None):
                continue
            if any(x in f"{title} {src}".lower() for x in excl):
                continue
            snip = html.unescape(e.get("summary", ""))
            snip = re.sub(r"<font[^>]*>.*?</font>", " ", snip, flags=re.S)
            snip = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", snip))).strip()[:500]
            if bad(title, src, snip):
                dropped["ausgeschlossen"] = dropped.get("ausgeschlossen", 0) + 1
                continue
            if not (job.get("open") and HAVE_AI) and not passes(job["rubric"], title, snip, job.get("trusted")):
                dropped[job["rubric"]] = dropped.get(job["rubric"], 0) + 1
                continue
            pub = dt.datetime(*e.published_parsed[:6], tzinfo=dt.timezone.utc)
            if pub < cutoff:
                continue
            iid = hashlib.sha1(f"{job['lang']}|{norm(title)}".encode()).hexdigest()[:12]
            countries = set()
            if job["country"]:
                countries.add(job["country"])
            if iid in db:
                it = db[iid]
                it["countries"] = sorted(set(it["countries"]) | countries)
                it["rubrics"] = sorted(set(it.get("rubrics") or [it["rubric"]]) | {job["rubric"]})
                it.setdefault("snippet", snip)
                if job.get("trusted"):
                    it["trusted"] = True
                if job.get("kunde"):
                    it["kunde"] = True
                if order.get(job["rubric"], 99) < order.get(it["rubric"], 99):
                    it["rubric"] = job["rubric"]
            else:
                db[iid] = dict(id=iid, title_orig=title, title_de=title if job["lang"] == "de" else None,
                               lang=job["lang"], source=src or "?", url=e.get("link", ""),
                               published=pub.isoformat(), rubric=job["rubric"], rubrics=[job["rubric"]],
                               countries=sorted(countries), snippet=snip, trusted=bool(job.get("trusted")), open=bool(job.get("open")), kunde=bool(job.get("kunde")))
    print("Firmensuchen (Firmen mit Treffern/gesamt):", {k: f"{len(v[0])}/{len(v[1])}" for k, v in firms.items()} or "keine")
    print(f"{ok}/{len(jobs)} Abfragen lieferten Treffer, Archiv: {len(db)} Meldungen")
    print("Durch Titel-Filter verworfen:", dropped or "nichts")

    items = [i for i in db.values() if dt.datetime.fromisoformat(i["published"]) >= cutoff]
    items.sort(key=lambda i: i["published"], reverse=True)
    NEWS.write_text(json.dumps(dict(meta=dict(updated=now.isoformat(), sample=False, health=dict(queries=base[1], ok=base[0], langs=langs, firms={k: [len(v[0]), len(v[1])] for k, v in firms.items()})), items=items),
                               ensure_ascii=False, indent=1), encoding="utf-8")
    if ok == 0:
        sys.exit("Keine einzige Abfrage erfolgreich – Netzwerk prüfen.")


if __name__ == "__main__":
    main()
