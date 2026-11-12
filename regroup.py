#!/usr/bin/env python3
"""Gruppiert die Vorfälle im Archiv neu (kostenlos, ohne Claude): für Test und Feinjustierung der Schwelle.
Aufruf im Workflow-Modus „nur Seite neu bauen“. Optional: GROUP_THRESHOLD / GROUP_MAX als Umgebungsvariablen."""
import collections
import json
import os
from pathlib import Path

import yaml

import ai
import grouping

NEWS = Path(__file__).parent / "data" / "news.json"
CFG = yaml.safe_load((Path(__file__).parent / "config.yaml").read_text(encoding="utf-8"))["ai"]


def main():
    d = json.loads(NEWS.read_text(encoding="utf-8"))
    if d["meta"].get("sample"):
        return
    thr = float(os.environ.get("GROUP_THRESHOLD") or CFG.get("group_threshold", 0.72))
    mx = int(os.environ.get("GROUP_MAX") or CFG.get("group_max", 8))
    ai.drop_oversized(d["items"])
    n = grouping.group_items(d["items"], thr=thr, max_size=mx)
    sizes = sorted(collections.Counter(i["grp"] for i in d["items"] if i.get("grp", "").startswith("g")).values(), reverse=True)
    print(f"Neu gruppiert (Schwelle {thr}, max {mx}): {n} Gruppen; Größen {sizes[:15]}; Verteilung {dict(sorted(collections.Counter(sizes).items()))}")
    NEWS.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
