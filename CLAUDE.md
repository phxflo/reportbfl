# Rope Report – Projektanleitung für Claude Code

Privates Tages-Dashboard „Rope Report“ für einen Export- und Regionalvertriebsleiter von Spezial-Stahldrahtseilen. Er liest es zur eigenen
Orientierung (PC, selten Handy) und leitet Maßnahmen selbst ab. Wichtig sind: Meldungen zu seinen Kunden, neue Projekte/Ausschreibungen und
die allgemeine Wirtschaftslage. Das Tool soll stark sein, aber wenig laufende Kosten verursachen. Kommunikation mit dem Nutzer: Deutsch, knapp.

## Aufbau
- GitHub Pages aus `docs/index.html`, per StaticCrypt passwortgeschützt. Repo `phxflo/reportbfl` ist **öffentlich**.
- `.github/workflows/update.yml` (Name „Seil-Report aktualisieren“): Cron (vier krumme Minuten, GitHub verzögert Zeitpläne oft um Stunden) + manueller Start.
  Eingaben: `rejudge`, `build_only` (Seite neu bauen ohne Suche/Claude, kostenlos – für Designänderungen).
- Ablauf: `fetch_ratings.py` → `fetch_news.py` (Google-News-RSS, Fachmedien, Firmensuchen) → `fetch_indices.py` (Destatis) → `ai.py` (Claude beurteilt Relevanz,
  übersetzt, fasst danach Dopplungen zu Geschichten zusammen: ein Aufruf je Lauf, `group_stories`) → `research.py` (Kurzbericht je angezeigter Meldung) → `build.py` (Template `templates/index.html.j2`) → `protect.py`.
- Archiv `data/news.enc` (AES, Passwort = Secret `PAGE_PASSWORD`); Klartext `data/news.json` nie committen.
- Konfiguration (Rubriken, Suchbegriffe, Limits) in `config.yaml`. Kunden-/Wettbewerberlisten nur als GitHub-Secrets `CUSTOMERS`/`COMPETITORS`
  (Format „Firma Land“ oder „Firma | website“); nie in Repo, Logs oder Commit-Texte schreiben.
- Design: Apple-Stil, festgehalten in `DESIGN.md` (Tokens: `.impeccable/design.json`), Produkt in `PRODUCT.md`; Werkzeug: Impeccable-Skill (`/impeccable critique|polish …`).
- Ampel-Bewertungen: Seite → Kommentare in Issue #36 → `data/ratings.json` (nicht im Repo). Rot blendet aus, Bewertungen gehen als Beispiele an Claude. Keine Embeddings (bewusst entfernt).

## Feste Entscheidungen des Nutzers
- 11 Kundenländer: BE, NL, MA, DZ, TN, IL, TR, GH, CI, LY, NG.
- Seitenaufbau: Kennzahlen · Zielmärkte (Häfen, Krane, Industrie, Spezialtiefbau als 2×2-Kacheln) · Markt & Handel (Wettbewerb, Handel & Rohstoffe) · Systemstatus.
  Keine Top-5, keine Projekte-Rubrik (Projekte/Ausschreibungen gehören in den jeweiligen Zielmarkt), keine Länderkarte/-filter, keine Suche, keine Erklärtexte, nur Text.
- Jede Meldung steht genau einmal. Pro Rubrik höchstens 5 (Wettbewerb 3), Mindest-Brisanz 4. Kundenmeldungen umgehen Limit und Mindest-Brisanz
  und gehören in einen Zielmarkt (nie in „Wettbewerb“). Nur von Claude beurteilte Meldungen werden angezeigt.
- Zu jeder angezeigten Meldung ein kurzer deutscher „Hintergrund“ (1–2 Sätze, kein Vorgehen, vollständig).
- NEU = seit gestern 06:30 Berlin veröffentlicht. Länder als graue Schrift, nur NEU/Kunde als Pillen.
- Wettbewerber-Ereignisse (Insolvenz, Streik, C-Level, Schließung, Neuigkeiten) sind wichtig (Brisanz 5).
- Offen/gewünscht: Wirtschaftslage-Block pro Kundenland (kostenlose Zahlen: Weltbank/IWF/Eurostat/worldsteel), Kunden-Bereich oben, ggf. Tageslage.

## Kosten (Nutzer achtet stark darauf)
- Claude API: Sonnet 5.5 beurteilt (`ai.max_items` 150/Lauf, erst Vorfilter, Kunden-/Wettbewerberquellen zuerst), Sonnet fasst auch Dopplungen zusammen (ein Aufruf, nur Titel, ca. 3–6 Cent), Haiku 5.5 übersetzt und schreibt Berichte mit Websuche (`research.max_per_run` 35).
- Jeder volle Lauf kostet Geld; Designänderungen immer mit `build_only` testen/ausrollen. Tageskosten in der Anthropic-Console prüfen.

## Arbeitsregeln
- Nie mergen, während ein Lauf läuft (sonst gehen Urteile verloren): vorher `gh run list --workflow update.yml --limit 1` prüfen.
- Ablauf für Änderungen: Branch → lokal `python make_sample.py && python build.py` (Beispielseite in `docs/index.html`, im Browser ansehen; danach
  `git checkout docs/index.html data/indices.json`) → `python test_rules.py` → `python -m pyflakes *.py` → PR → mergen.
- Logs enthalten nie Inhalte (Titel, Firmennamen), nur Zahlen. Analysen mit Echtdaten laufen als temporärer Workflow in Actions (Push-Trigger auf Testbranch,
  Archiv mit `PAGE_PASSWORD` entschlüsseln, nur Zahlen ausgeben), danach Branch löschen.
- Code schlank halten: Totes sofort entfernen, keine Reste alter Features, kein Mehraufwand ohne Nutzen. Nach CSS-Änderungen Klammerbilanz/Screenshot prüfen.
- Pakete: `pip install -r requirements.txt`.

## Offene Punkte
- Zeitplan-Verzögerung (Läufe starten gegen 12:30 statt 06:30): externer Wecker (cron-job.org → `workflow_dispatch` per Token) oder Raspberry Pi + Tailscale.
- Kosten-Zeile/Tageslimit im Systemstatus. Optional: trafilatura (Volltext für Berichte), GDELT als Zusatzquelle,
  Tageslage, Qualitäts-Check durch zweiten Agenten, Repo privat stellen.
