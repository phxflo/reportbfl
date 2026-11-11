#!/usr/bin/env python3
"""Übersetzt Überschriften ins Deutsche – gebündelt (viele Titel pro Anfrage), damit der kostenlose
Google-Dienst möglichst wenig Anfragen sieht. Darf den Build nie verhindern."""
import re
import sys
import time

LANGMAP = {"he": "iw"}


def _translator(lang):
    from deep_translator import GoogleTranslator
    try:
        return GoogleTranslator(source=LANGMAP.get(lang, lang), target="de")
    except Exception:
        return GoogleTranslator(source="auto", target="de")


def _chunks(items, limit=4200):
    cur, size = [], 0
    for i in items:
        n = len(i["title_orig"]) + 1
        if cur and size + n > limit:
            yield cur
            cur, size = [], 0
        cur.append(i)
        size += n
    if cur:
        yield cur


def translate_titles(items):
    """Setzt item['title_de'] für alle übergebenen Meldungen (soweit der Dienst antwortet). Gibt die Anzahl zurück."""
    groups = {}
    for i in items:
        groups.setdefault(i["lang"], []).append(i)
    done = fails = 0
    for lang, group in groups.items():
        tr = _translator(lang)
        for chunk in _chunks(group):
            ok = False
            for attempt in range(3):
                try:
                    text = "\n".join(re.sub(r"\s+", " ", i["title_orig"]) for i in chunk)
                    lines = (tr.translate(text) or "").split("\n")
                    if len(lines) != len(chunk):
                        raise ValueError(f"Zeilenzahl {len(lines)} != {len(chunk)}")
                    for i, line in zip(chunk, lines):
                        if line.strip():
                            i["title_de"] = line.strip()
                            done += 1
                    ok = True
                    break
                except Exception as ex:
                    print(f"  Übersetzung {lang} Versuch {attempt + 1}/3: {ex}", file=sys.stderr)
                    time.sleep(3 * (attempt + 1))
            if not ok:                                   # Ersatz: einzeln (begrenzt)
                for i in chunk[:15]:
                    try:
                        out = tr.translate(i["title_orig"])
                        if out:
                            i["title_de"] = out
                            done += 1
                    except Exception:
                        break
                    time.sleep(0.4)
                fails += 1
                if fails >= 4:
                    print("  Übersetzung abgebrochen (zu viele Fehler)", file=sys.stderr)
                    return done
            else:
                fails = 0
            time.sleep(1.0)
    return done
