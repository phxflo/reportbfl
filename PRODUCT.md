# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
One reader: an export and regional sales manager for special steel wire ropes. He opens the page each morning before his first calls, mostly on a desktop PC, rarely on a phone, to get oriented; he decides on actions himself.

## Product Purpose
"Rope Report" is a private, password-protected daily news dashboard. It collects news, lets Claude keep only what matters, merges duplicates into one story, and adds a short German background note to each item. Success: within seconds he knows what happened at his customers, which projects and tenders appeared in his target markets, and how trade measures, raw material prices and competitors are moving.

## Positioning
Built for one person's territory: eleven customer countries (BE, NL, MA, DZ, TN, IL, TR, GH, CI, LY, NG), four target markets (ports, cranes, steel/heavy industry, special foundation engineering), his own customer and competitor lists (kept secret, never in the repo).

## Operating Context
Generated once a day by GitHub Actions as a single static HTML page (Jinja template `templates/index.html.j2`, built by `build.py`), encrypted with StaticCrypt and served by GitHub Pages. Read in a browser; follows the system light/dark setting. Design changes are rolled out with the free `build_only` run.

## Capabilities and Constraints
- Fixed structure (owner's decision): Kennzahlen (Destatis charts) · Zielmärkte as 2×2 tiles (Häfen, Krane, Industrie, Spezialtiefbau) · Markt & Handel (Wettbewerb, Zölle & Tarife, Rohstoffe) · Systemstatus.
- Each item appears once; at most 5 per section (3 for Zölle, Rohstoffe, Wettbewerb); customer items always shown, never under Wettbewerb.
- Countries in grey text; only "NEU" and "Kunde" as pills. Each item: collapsible "Hintergrund", green/yellow/red rating that trains the filter.
- No top list, no projects section, no country map or filter, no search, no explanatory texts, text only (no photos or icons as content).
- Page is a single self-contained file: fonts embedded, no external requests, no JavaScript frameworks.
- Running costs must stay low; the page itself costs nothing to rebuild.

## Brand Commitments
- Name "Rope Report", the wire-rope cross-section mark.
- One fixed colour per section (Häfen, Krane, Industrie, Spezialtiefbau, Wettbewerb, Zölle, Rohstoffe), always paired with its label.
- Automatic light and dark mode.
- Visual standard (owner's choice): the classic Apple product-page style, played straight at full craft; Apple's own pages and apps set the bar.

## Evidence on Hand
Real content only from the daily run (encrypted archive). The sample page from `make_sample.py` uses invented "Beispiel:" headlines and is labelled as such.

## Product Principles
1. Today first: what changed since yesterday must be findable in seconds.
2. Customers above everything: a customer item is never hidden by limits.
3. Calm and trustworthy: one reader, every morning; no noise, no alarm without cause.
4. Text carries the meaning; design supports reading, never decorates.
