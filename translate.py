#!/usr/bin/env python3
"""Übersetzt Überschriften ins Deutsche – offline, ohne Konto, ohne Ratenbegrenzung.

Nutzt die freien Argos-Modelle (OpenNMT/CTranslate2). Die Modelle werden beim ersten Lauf geladen
(je ~50–100 MB) und im Ordner .cache/argos abgelegt. Übersetzt wird über Englisch: fr/nl/tr/ar/he/es → en → de.
Englisch und Deutsch werden nicht übersetzt. Darf den Build nie verhindern: bei Fehlern bleibt der Originaltitel
stehen und der Browser (Chrome) kann ihn noch übersetzen."""
import glob
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

CACHE = Path(__file__).parent / ".cache" / "argos"
INDEX = "https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json"
FALLBACK = {   # falls der Index nicht erreichbar ist
    "fr-en": "https://argos-net.com/v1/translate-fr_en-1_9.argosmodel",
    "nl-en": "https://argos-net.com/v1/translate-nl_en-1_8.argosmodel",
    "tr-en": "https://argos-net.com/v1/translate-tr_en-1_5.argosmodel",
    "ar-en": "https://argos-net.com/v1/translate-ar_en-1_0.argosmodel",
    "he-en": "https://argos-net.com/v1/translate-he_en-1_5.argosmodel",
    "es-en": "https://argos-net.com/v1/translate-es_en-1_9.argosmodel",
    "en-de": "https://argos-net.com/v1/translate-en_de-1_3.argosmodel",
}
SKIP = {"de", "en"}
_index = None
_models = {}


def _links():
    global _index
    if _index is None:
        _index = dict(FALLBACK)
        try:
            with urllib.request.urlopen(INDEX, timeout=30) as r:
                for p in json.load(r):
                    key = f"{p['from_code']}-{p['to_code']}"
                    if key in FALLBACK and p.get("links"):
                        _index[key] = p["links"][0]
        except Exception as ex:
            print(f"  Argos-Index nicht erreichbar, nutze feste Adressen ({ex})", file=sys.stderr)
    return _index


def _load(pair):
    """Gibt (Translator, SentencePiece) für ein Sprachpaar zurück; lädt das Modell bei Bedarf."""
    if pair in _models:
        return _models[pair]
    import ctranslate2
    import sentencepiece as spm
    folder = CACHE / pair
    if not glob.glob(str(folder / "**" / "sentencepiece.model"), recursive=True):
        folder.mkdir(parents=True, exist_ok=True)
        url = _links()[pair]
        print(f"  lade Übersetzungsmodell {pair} …", file=sys.stderr)
        tmp = folder / "m.zip"
        urllib.request.urlretrieve(url, tmp)
        with zipfile.ZipFile(tmp) as z:
            z.extractall(folder)
        tmp.unlink()
    sp_path = glob.glob(str(folder / "**" / "sentencepiece.model"), recursive=True)[0]
    root = Path(sp_path).parent
    model_dir = next(p.parent for p in root.rglob("model.bin"))
    tr = ctranslate2.Translator(str(model_dir), device="cpu", inter_threads=1, intra_threads=2)
    sp = spm.SentencePieceProcessor(model_file=sp_path)
    _models[pair] = (tr, sp)
    return _models[pair]


def _run(pair, texts):
    tr, sp = _load(pair)
    out = []
    for k in range(0, len(texts), 32):
        batch = texts[k:k + 32]
        toks = [sp.encode(t, out_type=str) for t in batch]
        res = tr.translate_batch(toks, beam_size=4, max_decoding_length=160, repetition_penalty=1.1)
        out += [sp.decode(r.hypotheses[0]).strip() for r in res]
    return out


def translate_titles(items):
    """Setzt item['title_de'] für alle fremdsprachigen Meldungen (soweit möglich). Gibt die Anzahl zurück."""
    groups = {}
    for i in items:
        if i["lang"] not in SKIP and not i.get("title_de"):
            groups.setdefault(i["lang"], []).append(i)
    done = 0
    for lang, group in groups.items():
        try:
            texts = [re.sub(r"\s+", " ", i["title_orig"]).strip() for i in group]
            en = _run(f"{lang}-en", texts)
            de = _run("en-de", en)
            for i, t in zip(group, de):
                if t:
                    i["title_de"] = t
                    done += 1
        except Exception as ex:
            print(f"  Übersetzung {lang} fehlgeschlagen: {ex}", file=sys.stderr)
    return done


if __name__ == "__main__":
    demo = [dict(lang="fr", title_orig="Le port de Tanger Med commande de nouvelles grues"),
            dict(lang="tr", title_orig="İzmir'de demir çelik fabrikasında patlama: 17 ölü"),
            dict(lang="nl", title_orig="Staking in de haven van Antwerpen aangekondigd")]
    print(translate_titles(demo))
    for d in demo:
        print(d.get("title_de"))
