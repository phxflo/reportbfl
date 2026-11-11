# Der Seil-Report

Tägliches News-Dashboard für Industrie-Stahlseile (Export & Regionalvertrieb).

| Datei | Zweck |
|---|---|
| `config.yaml` | Rubriken, Suchbegriffe je Sprache, Länder, Kennzahlen – hier anpassen |
| `fetch_news.py` | Holt Meldungen (Google News RSS, 7 Sprachen), übersetzt Titel ins Deutsche |
| `fetch_indices.py` | Holt Kennzahlen aus Destatis GENESIS (Zugangsdaten als GitHub-Secrets) |
| `build.py` + `templates/` | Baut `docs/index.html` |
| `make_sample.py` | Erzeugt Beispieldaten für eine Design-Vorschau (nur lokal nötig) |
| `.github/workflows/update.yml` | Täglicher automatischer Lauf |

Lokal testen: `pip install -r requirements.txt && python make_sample.py && python build.py`, dann `docs/index.html` öffnen.
