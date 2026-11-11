#!/usr/bin/env python3
"""Holt Meldungen per Google-News-RSS (alle Sprachen), ordnet sie Rubriken/Ländern zu,
übersetzt Titel ins Deutsche und pflegt das Archiv data/news.json."""
import datetime as dt
import hashlib
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

import feedparser
import requests
import yaml

ROOT = Path(__file__).parent
CFG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
NEWS = ROOT / "data" / "news.json"
UA = {"User-Agent": "Mozilla/5.0 (compatible; SeilReport/1.0)"}
MAX_TRANSLATE = 1500


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


def build_jobs(days):
    jobs = []
    for r in CFG["rubrics"]:
        for lang, terms in (r.get("terms") or {}).items():
            for ed in CFG["editions"][lang]:
                for grp in chunks(terms, 7):
                    q = "(" + " OR ".join(quote_term(t) for t in grp) + ")"
                    jobs.append(dict(url=feed_url(q, ed["hl"], ed["gl"], ed["ceid"], days),
                                     rubric=r["id"], lang=lang, country=None))
    for c in CFG["countries"]:
        for e in c["editions"]:
            jobs.append(dict(url=feed_url(e["q"], e["hl"], e["gl"], e["ceid"], days),
                             rubric="laender", lang=e["lang"], country=c["id"]))
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
            print(f"  Fehler: {e}", file=sys.stderr)
        time.sleep(2 * (i + 1))
    return None


def detect_countries(text):
    low = text.lower()
    return [c["id"] for c in CFG["countries"] if any(n.lower() in low for n in c["names"])]


def main():
    days = CFG["site"]["fetch_days"]
    keep = CFG["site"]["retention_days"]
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=keep)
    excl = [e.lower() for e in CFG.get("exclude", [])]
    order = {r["id"]: i for i, r in enumerate(CFG["rubrics"])}

    db = {}
    if NEWS.exists():
        old = json.loads(NEWS.read_text(encoding="utf-8"))
        if not old.get("meta", {}).get("sample"):
            db = {i["id"]: i for i in old.get("items", [])}

    jobs = build_jobs(days)
    print(f"{len(jobs)} Abfragen …")
    ok = 0
    for n, job in enumerate(jobs, 1):
        feed = fetch(job["url"])
        time.sleep(1.0)
        if not feed or not feed.entries:
            continue
        ok += 1
        for e in feed.entries:
            raw = e.get("title", "").strip()
            src = (e.get("source") or {}).get("title") or job.get("source") or ""
            title = raw[: -len(src) - 3] if src and raw.endswith(f" - {src}") else raw
            if not title or not getattr(e, "published_parsed", None):
                continue
            if any(x in title.lower() for x in excl):
                continue
            pub = dt.datetime(*e.published_parsed[:6], tzinfo=dt.timezone.utc)
            if pub < cutoff:
                continue
            iid = hashlib.sha1(f"{job['lang']}|{norm(title)}".encode()).hexdigest()[:12]
            countries = set(detect_countries(title))
            if job["country"]:
                countries.add(job["country"])
            if iid in db:
                it = db[iid]
                it["countries"] = sorted(set(it["countries"]) | countries)
                if order.get(job["rubric"], 99) < order.get(it["rubric"], 99):
                    it["rubric"] = job["rubric"]
            else:
                db[iid] = dict(id=iid, title_orig=title, title_de=title if job["lang"] == "de" else None,
                               lang=job["lang"], source=src or "?", url=e.get("link", ""),
                               published=pub.isoformat(), rubric=job["rubric"],
                               countries=sorted(countries))
    print(f"{ok}/{len(jobs)} Abfragen lieferten Treffer, Archiv: {len(db)} Meldungen")

    # Neueste zuerst übersetzen; bei Fehlern wiederholen, erst nach 5 Totalausfällen in Folge abbrechen
    todo = sorted([i for i in db.values() if not i.get("title_de")],
                  key=lambda i: i["published"], reverse=True)[:MAX_TRANSLATE]
    if todo:
        from deep_translator import GoogleTranslator
        tr, fails, done = GoogleTranslator(source="auto", target="de"), 0, 0
        for i in todo:
            for attempt in range(3):
                try:
                    out = tr.translate(i["title_orig"])
                    if out:
                        i["title_de"] = out
                        done += 1
                    fails = 0
                    break
                except Exception as ex:  # Übersetzung ist "nice to have"
                    print(f"  Übersetzung fehlgeschlagen ({attempt + 1}/3): {ex}", file=sys.stderr)
                    time.sleep(2 * (attempt + 1))
            else:
                fails += 1
                if fails >= 5:
                    print("  Übersetzung abgebrochen (5 Fehler in Folge)", file=sys.stderr)
                    break
            time.sleep(0.15)
        print(f"{done} von {len(todo)} Titeln übersetzt")

    items = [i for i in db.values() if dt.datetime.fromisoformat(i["published"]) >= cutoff]
    items.sort(key=lambda i: i["published"], reverse=True)
    NEWS.write_text(json.dumps(dict(meta=dict(updated=now.isoformat(), sample=False), items=items),
                               ensure_ascii=False, indent=1), encoding="utf-8")
    if ok == 0:
        sys.exit("Keine einzige Abfrage erfolgreich – Netzwerk prüfen.")


if __name__ == "__main__":
    main()
