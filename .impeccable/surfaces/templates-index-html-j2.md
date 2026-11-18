---
version: 1
slug: "templates-index-html-j2"
primary_target: "templates/index.html.j2"
related_targets: []
---

# Surface: Rope-Report-Tagesseite

Scope: the whole page `templates/index.html.j2` (rendered by build.py). Mode: Operate (daily briefing read and triaged by one person). Audience/job: the sales manager at his desk at 7:30, scanning what changed for customers, target markets and trade before his first call; rates items green/yellow/red. Constraints: structure, content, section colours, rope mark and automatic light/dark from PRODUCT.md stay; text only; single self-contained file. Chosen direction: the category standard (Apple product-page style), taken by the owner as the standing exit.

## Direction contract
THESIS: The page reads like an Apple product page: big confident headlines per group, white rounded surfaces floating on a soft grey ground, generous air, nothing decorative. It refuses the grey admin-dashboard look with bordered boxes and small grey kickers.
OWN-WORLD: Light ground #f5f5f7, white cards radius 18px with a soft offset shadow and no border; dark: black ground, #1c1c1e cards. Ink #1d1d1f, secondary #6e6e73. Apple system blue for links, focus and chart lines; orange "NEU", dark "Kunde" capsule. Section colours tuned to Apple's system palette as small dots. SF Pro on Apple devices, embedded Inter elsewhere; tight negative tracking on headlines, tabular numerals.
STORY: He sees the date and status, jumps via the translucent bar, reads each group headline, scans list rows separated by inset hairlines, opens "Hintergrund" when needed, rates and moves on.
FIRST VIEWPORT: Large "Rope Report" title left with the mark, "Stand" right; translucent sticky bar with segmented-control style capsules; "Kennzahlen" 34px headline, two large chart cards side by side with 40px values.
FORM: canon (standing exit), position: category standard; seed:5f9de292fd8c6e9e (degraded roll, no challengers).
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
