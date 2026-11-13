#!/usr/bin/env python3
"""Verschlüsselt die fertige Seite (docs/index.html) mit dem Passwort aus der Umgebungsvariable PAGE_PASSWORD
(StaticCrypt: AES-256, im Browser entschlüsselt). Bricht ab, wenn kein Passwort gesetzt ist – die Klartext-Seite
wird dann NICHT veröffentlicht."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PAGE = Path(__file__).parent / "docs" / "index.html"
SALT = "5e11a7b3c9d24f60a8b17d3e0c4f9a12"        # nicht geheim; fest, damit "Auf diesem Gerät merken" Läufe überdauert
MIN_LEN = 12


def main():
    pw = os.environ.get("PAGE_PASSWORD", "")
    if len(pw) < MIN_LEN:
        sys.exit(f"::error::PAGE_PASSWORD fehlt oder ist kürzer als {MIN_LEN} Zeichen – es wird nichts veröffentlicht.")
    out_dir = Path(tempfile.mkdtemp())
    env = dict(os.environ, STATICRYPT_PASSWORD=pw)
    cmd = ["npx", "--yes", "staticrypt@3.5.4", str(PAGE), "-c", "false", "-d", str(out_dir), "-s", SALT, "--short",
           "--remember", "30", "--template-title", "Rope Report", "--template-button", "Öffnen",
           "--template-placeholder", "Passwort", "--template-remember", "Auf diesem Gerät merken",
           "--template-error", "Falsches Passwort", "--template-instructions", "Geschützter Bereich",
           "--template-color-primary", "#1a2b3c", "--template-color-secondary", "#6ec6f5"]
    subprocess.run(cmd, check=True, env=env)
    enc = (out_dir / PAGE.name).read_text(encoding="utf-8")
    # Sicherheitsnetz: im Ergebnis darf kein lesbarer Seiteninhalt stehen
    for probe in ("Report</span></h1>", "data-id=", "Kennzahlen"):
        if probe in enc:
            sys.exit("::error::Verschlüsselung fehlgeschlagen – Klartext im Ergebnis. Es wird nichts veröffentlicht.")
    enc = enc.replace('<meta charset="utf-8" />', '<meta charset="utf-8" />\n        <meta name="robots" content="noindex,nofollow" />', 1)
    shutil.copyfile(PAGE, PAGE.with_name("plain.tmp"))   # nur lokal, wird gleich gelöscht
    PAGE.write_text(enc, encoding="utf-8")
    PAGE.with_name("plain.tmp").unlink()
    print(f"Seite verschlüsselt ({len(enc) // 1024} kB)")


if __name__ == "__main__":
    main()
