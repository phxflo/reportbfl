#!/usr/bin/env python3
"""Liest die Ampel-Bewertungen aus den Kommentaren eines GitHub-Issues (Quelle der Wahrheit) und legt sie als
data/ratings.json ab ({id: {r: g|y|r, t: Zeitstempel}}). Nur Kommentare des Repo-Inhabers zählen.
Die Datei ist nur Zwischenspeicher (nicht im Repo), nur IDs und Wertungen kommen aus dem öffentlichen Issue."""
import json
import os
import sys
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).parent
OUT = ROOT / "data" / "ratings.json"


def main():
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))["site"].get("rating") or {}
    repo, issue = os.environ.get("GITHUB_REPOSITORY") or cfg.get("repo"), cfg.get("issue")
    token = os.environ.get("GITHUB_TOKEN", "")
    owner = (os.environ.get("GITHUB_REPOSITORY_OWNER") or (repo or "/").split("/")[0]).lower()
    OUT.parent.mkdir(exist_ok=True)
    out = {}
    if not (repo and issue):
        OUT.write_text("{}", encoding="utf-8")
        return
    page, n = 1, 0
    while page < 40:
        try:
            r = requests.get(f"https://api.github.com/repos/{repo}/issues/{issue}/comments",
                             params=dict(per_page=100, page=page),
                             headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"} if token else {}, timeout=30)
        except requests.RequestException as e:
            print("Bewertungen nicht lesbar:", type(e).__name__, file=sys.stderr)
            break
        if r.status_code != 200:
            print("Bewertungen nicht lesbar: HTTP", r.status_code, file=sys.stderr)
            break
        rows = r.json()
        for c in rows:
            if (c.get("user") or {}).get("login", "").lower() != owner:
                continue
            try:
                for x in json.loads(c["body"]):
                    if x.get("r") in ("g", "y", "r") and isinstance(x.get("i"), str) and len(x["i"]) <= 20:
                        n += 1
                        if x["i"] not in out or int(x.get("t", 0)) >= out[x["i"]]["t"]:
                            out[x["i"]] = dict(r=x["r"], t=int(x.get("t", 0)))
            except (ValueError, TypeError, KeyError):
                continue
        if len(rows) < 100:
            break
        page += 1
    OUT.write_text(json.dumps(out), encoding="utf-8")
    g = sum(1 for v in out.values() if v["r"] == "g"); y = sum(1 for v in out.values() if v["r"] == "y"); rd = sum(1 for v in out.values() if v["r"] == "r")
    print(f"Bewertungen: {len(out)} Meldungen bewertet (grün {g}, gelb {y}, rot {rd})")


if __name__ == "__main__":
    main()
