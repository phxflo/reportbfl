#!/usr/bin/env python3
"""Holt die Kennzahlen aus Destatis GENESIS-Online und schreibt data/indices.json.

Zugangsdaten (kostenlose Registrierung bei Destatis) kommen aus den Umgebungsvariablen
DESTATIS_USER und DESTATIS_PASSWORD (bei Token-Zugang: Token als USER, PASSWORD leer lassen).
Schlägt der Abruf fehl, bleiben die bisherigen Werte erhalten.
"""
import csv
import datetime as dt
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).parent
CFG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
OUT = ROOT / "data" / "indices.json"
API = "https://genesis.destatis.de/genesisWS/rest/2020/data/tablefile"
DEBUG = "--debug" in sys.argv


def fetch_table(name):
    user, pw = os.environ.get("DESTATIS_USER", ""), os.environ.get("DESTATIS_PASSWORD", "")
    if not user:
        raise RuntimeError("DESTATIS_USER nicht gesetzt")
    headers = {"Content-Type": "application/x-www-form-urlencoded", "username": user, "password": pw}
    data = dict(name=name, area="all", format="ffcsv", language="de")
    url = API
    for _ in range(4):                      # Weiterleitungen selbst folgen, damit es bei POST bleibt
        r = requests.post(url, headers=headers, data=data, timeout=(30, 300), allow_redirects=False)
        if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("Location"):
            url = requests.compat.urljoin(url, r.headers["Location"])
            continue
        break
    r.raise_for_status()
    raw = r.content
    if raw[:2] == b"PK":                    # ffcsv kommt als ZIP mit einer CSV-Datei darin
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            member = next((n for n in z.namelist() if n.lower().endswith((".csv", ".txt"))), z.namelist()[0])
            raw = z.read(member)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    if text.lstrip().startswith("{"):       # Fehlermeldung von Destatis (JSON) statt Tabelle
        try:
            st = json.loads(text).get("Status", {})
            raise RuntimeError(f"Destatis: {st.get('Content') or text[:200]} (Code {st.get('Code')})")
        except ValueError:
            pass
    return text


MONTHS = {"januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4, "mai": 5, "juni": 6, "juli": 7, "august": 8,
          "september": 9, "oktober": 10, "november": 11, "dezember": 12, "january": 1, "february": 2, "march": 3,
          "may": 5, "june": 6, "july": 7, "october": 10, "december": 12}


def period(joined, freq):
    """Erkennt die Periode in einer Zeile, egal ob als MONAT09/QUART3, 2025-09, 09/2025, 'September 2025' oder '3. Quartal 2025'."""
    y = re.search(r"\b((?:19|20)\d\d)\b", joined)
    if not y:
        return None
    year = y.group(1)
    low = joined.lower()
    if freq == "monthly":
        m = (re.search(r"monat(\d\d)", low) or re.search(r"\b(?:19|20)\d\d-(\d\d)(?:-\d\d)?\b", joined)
             or re.search(r"\b(\d\d?)/(?:19|20)\d\d\b", joined))
        if m and 1 <= int(m.group(1)) <= 12:
            return f"{year}-{int(m.group(1)):02d}"
        for name, num in MONTHS.items():
            if re.search(rf"\b{name}\b", low):
                return f"{year}-{num:02d}"
        return None
    q = (re.search(r"quart(\d)", low) or re.search(r"\b([1-4])\. ?quartal", low) or re.search(r"\bq([1-4])\b", low)
         or re.search(r"\b(?:19|20)\d\d-q([1-4])\b", low))
    return f"{year}-Q{q.group(1)}" if q else None


def parse(text, spec):
    """Liest die flache CSV und sammelt (Periode, Wert). Bewusst tolerant gegenüber Spaltennamen und Zeitformaten."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    rows = [r for r in csv.reader(io.StringIO(text, newline=""), delimiter=";") if r]
    header = [h.strip().lower() for h in rows[0]]
    if DEBUG:
        print("Kopfzeile:", header, "\nBeispiel:", rows[1:3], file=sys.stderr)
    vcol = next((i for i, h in enumerate(header) if h in ("value", "wert")), len(header) - 1)
    pts = {}
    for row in rows[1:]:
        joined = ";".join(row)
        if not all(tok in joined for tok in spec["require"]):
            continue
        cell = row[vcol].strip() if vcol < len(row) else ""
        try:
            v = float(cell.replace(".", "").replace(",", ".")) if "," in cell else float(cell)
        except ValueError:
            continue
        per = period(";".join(c for i, c in enumerate(row) if i != vcol), spec["freq"])
        if per:
            pts[per] = v
    return [dict(p=p, v=pts[p]) for p in sorted(pts)]


def save_raw(name, text):
    """Legt die ersten Zeilen der Destatis-Antwort ab (öffentliche Statistikdaten), damit das Format prüfbar ist."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    seen = []
    for ln in lines[1:]:
        for c in ln.split(";"):
            if re.fullmatch(r"(GP19-\d+|WZ08-[A-Z0-9]+|WERT\w*)", c) and c not in seen:
                seen.append(c)
    codes = " ".join(seen[:80])
    (ROOT / "data" / f"raw_{name}.txt").write_text(f"{len(lines)} Zeilen insgesamt\n" + "\n".join(lines[:25]) + "\n" + "CODES: " + codes + "\n",
                                                  encoding="utf-8")


def main():
    old = {}
    if OUT.exists():
        data = json.loads(OUT.read_text(encoding="utf-8"))
        if not data.get("meta", {}).get("sample"):
            old = data.get("series", {})
    series, errors = dict(old), []
    for spec in CFG["indices"]:
        tried, ok = [], False
        for table in spec.get("tables") or [spec["table"]]:
            for req in [spec["require"]] + ([spec["fallback_require"]] if spec.get("fallback_require") else []):
                try:
                    text = fetch_table(table)
                    save_raw(f"{spec['id']}_{table}", text)
                    pts = parse(text, dict(spec, require=req))
                except Exception as ex:
                    tried.append(f"{table}: {str(ex)[:80]}")
                    break
                if len(pts) >= 4:
                    series[spec["id"]] = dict(points=pts, fetched=dt.date.today().isoformat(), table=table,
                                              note=spec.get("fallback_note", "") if req is not spec["require"] else "")
                    print(f"{spec['id']}: {table} {req} → {len(pts)} Punkte, zuletzt {pts[-1]}")
                    ok = True
                    break
                tried.append(f"{table} {req}: {len(pts)} Punkte")
            if ok:
                break
        if not ok:
            errors.append(f"{spec['id']}: keine Daten ({'; '.join(tried)})")
            print(f"FEHLER {spec['id']}: {tried}", file=sys.stderr)
    OUT.write_text(json.dumps(dict(meta=dict(sample=False, errors=errors), series=series),
                              ensure_ascii=False, indent=1), encoding="utf-8")
    # Nicht abbrechen: Dashboard soll auch ohne Kennzahlen-Update erscheinen.


if __name__ == "__main__":
    main()
