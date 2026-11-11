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
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).parent
CFG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
OUT = ROOT / "data" / "indices.json"
API = "https://www-genesis.destatis.de/genesisWS/rest/2020/data/tablefile"
DEBUG = "--debug" in sys.argv


def fetch_table(name):
    user, pw = os.environ.get("DESTATIS_USER", ""), os.environ.get("DESTATIS_PASSWORD", "")
    if not user:
        raise RuntimeError("DESTATIS_USER nicht gesetzt")
    r = requests.get(API, params=dict(name=name, area="all", format="ffcsv", language="de"),
                     headers=dict(username=user, password=pw), timeout=60)
    r.raise_for_status()
    return r.content.decode("utf-8-sig", errors="replace")


def parse(text, spec):
    """Liest die flache CSV und sammelt (Periode, Wert). Bewusst tolerant gegenüber Spaltennamen."""
    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    header = [h.strip().lower() for h in rows[0]]
    if DEBUG:
        print("Kopfzeile:", header, "\nBeispiel:", rows[1:3], file=sys.stderr)
    vcol = next((i for i, h in enumerate(header) if h in ("value", "wert")), len(header) - 1)
    pts = {}
    for row in rows[1:]:
        joined = ";".join(row)
        if not all(tok in joined for tok in spec["require"]):
            continue
        try:
            v = float(row[vcol].replace(".", "").replace(",", ".")) if "," in row[vcol] else float(row[vcol])
        except (ValueError, IndexError):
            continue
        y = re.search(r"\b(19|20)\d\d\b", joined)
        if not y:
            continue
        if spec["freq"] == "monthly":
            m = re.search(r"MONAT(\d\d)", joined)
            if not m:
                continue
            per = f"{y.group(0)}-{m.group(1)}"
        else:
            q = re.search(r"QUART(\d)", joined)
            if not q:
                continue
            per = f"{y.group(0)}-Q{q.group(1)}"
        pts[per] = v
    return [dict(p=p, v=pts[p]) for p in sorted(pts)]


def main():
    old = {}
    if OUT.exists():
        data = json.loads(OUT.read_text(encoding="utf-8"))
        if not data.get("meta", {}).get("sample"):
            old = data.get("series", {})
    series, errors = dict(old), []
    for spec in CFG["indices"]:
        try:
            pts = parse(fetch_table(spec["table"]), spec)
            if len(pts) < 4:
                raise RuntimeError(f"nur {len(pts)} Datenpunkte erkannt – Parser/Filter prüfen (--debug)")
            series[spec["id"]] = dict(points=pts, fetched=dt.date.today().isoformat())
            print(f"{spec['id']}: {len(pts)} Punkte, zuletzt {pts[-1]}")
        except Exception as ex:
            errors.append(f"{spec['id']}: {ex}")
            print(f"FEHLER {spec['id']}: {ex}", file=sys.stderr)
    OUT.write_text(json.dumps(dict(meta=dict(sample=False, errors=errors), series=series),
                              ensure_ascii=False, indent=1), encoding="utf-8")
    # Nicht abbrechen: Dashboard soll auch ohne Kennzahlen-Update erscheinen.


if __name__ == "__main__":
    main()
