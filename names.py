"""Liest die vertraulichen Firmenlisten aus Umgebungsvariablen (GitHub-Secrets CUSTOMERS / COMPETITORS).
Eintrag: "Firma" oder "Firma | website.de", getrennt durch Komma oder Zeilenumbruch."""
import os
import re


def parse(var):
    out = []
    for raw in os.environ.get(var, "").replace("\n", ",").split(","):
        name, _, dom = raw.partition("|")
        name, dom = name.strip(), re.sub(r"^https?://|/.*$", "", dom.strip()).removeprefix("www.")
        if name:
            out.append((name, dom or None))
    return out


def only_names(var):
    return [n for n, _ in parse(var)]
