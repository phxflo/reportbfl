"""Liest die vertraulichen Firmenlisten aus Umgebungsvariablen (GitHub-Secrets CUSTOMERS / COMPETITORS).
Eintrag: "Firma Land" oder "Firma | website.de", getrennt durch Komma oder Zeilenumbruch.
Ein Landesname im Eintrag (deutsch, englisch, französisch oder Kürzel wie MA) wird abgetrennt und steuert die Suchausgaben."""
import os
import re

COUNTRY = {
    "BE": ["belgien", "belgium", "belgique", "belgië", "belgie"],
    "NL": ["niederlande", "netherlands", "nederland", "pays-bas", "pays bas", "holland", "the netherlands"],
    "MA": ["marokko", "morocco", "maroc"],
    "DZ": ["algerien", "algeria", "algérie", "algerie"],
    "TN": ["tunesien", "tunisia", "tunisie"],
    "IL": ["israel", "israël"],
    "TR": ["türkei", "tuerkei", "turkey", "türkiye", "turkiye", "turquie"],
    "GH": ["ghana"],
}
LEGAL = r"(?:n\.?v\.?|b\.?v\.?|s\.?a\.?(?:r\.?l\.?)?|gmbh(?: & co\.? kg)?|ag|a\.?ş\.?|as|ltd\.?|limited|inc\.?|llc|plc|s\.?p\.?a\.?|co\.?|corp\.?|sàrl|s\.?r\.?l\.?|kg)"


def split_country(name):
    """('Port X NV Marokko') -> ('Port X', 'MA')"""
    low = name.lower()
    for cid, words in COUNTRY.items():
        for w in sorted(words, key=len, reverse=True):
            m = re.search(rf"(?<![\w]){re.escape(w)}(?![\w])[\s\)\]\.,;\-–/]*$", low)   # Land steht am Ende des Eintrags
            if m:
                rest = name[:m.start()]
                return clean(rest), cid
        # Kürzel nur in Klammern oder nach Trennzeichen am Ende: "Name (MA)", "Name - MA"
        m = re.search(rf"[\(\-–/]\s*{cid}\s*\)?\s*$", name)
        if m:
            return clean(name[:m.start()]), cid
    return clean(name), None


def clean(name):
    name = re.sub(r"[\(\)\[\]]", " ", name)
    name = re.sub(r"\s[-–/]\s*$|^\s*[-–/]\s", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" -–/,.;")
    stripped = re.sub(rf"\s+{LEGAL}$", "", name, flags=re.I).strip(" -–/,.;")
    return stripped or name


def parse(var):
    """Liste von (Name, Website|None, Land|None)."""
    out = []
    for raw in os.environ.get(var, "").replace("\n", ",").split(","):
        name, _, dom = raw.partition("|")
        dom = re.sub(r"^https?://|/.*$", "", dom.strip()).removeprefix("www.")
        core, cid = split_country(name.strip())
        if not core and cid and out and out[-1][2] is None:      # "Firma, Marokko": Land gehört zum vorigen Eintrag
            out[-1] = (out[-1][0], out[-1][1], cid)
            continue
        if core:
            out.append((core, dom or None, cid))
    return out


def only_names(var):
    return [n for n, _, _ in parse(var)]
