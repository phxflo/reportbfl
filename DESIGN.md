---
name: Rope Report
description: Private daily news briefing for a steel-wire-rope sales territory, in the classic Apple product-page style.
colors:
  system-blue: "#0066cc"
  system-blue-dark: "#2997ff"
  new-orange: "#b64400"
  new-orange-dark: "#ff9f0a"
  new-orange-wash: "rgba(255,149,0,.14)"
  new-orange-wash-dark: "rgba(255,159,10,.16)"
  rope-core-amber: "#ff9f0a"
  ground: "#f5f5f7"
  ground-dark: "#000000"
  card: "#ffffff"
  card-dark: "#1c1c1e"
  ink: "#1d1d1f"
  ink-dark: "#f5f5f7"
  secondary-ink: "#6e6e73"
  secondary-ink-dark: "#a1a1a6"
  faint-ink-dark: "#8e8e93"
  hairline: "rgba(0,0,0,.09)"
  hairline-dark: "rgba(255,255,255,.1)"
  fill: "rgba(0,0,0,.05)"
  fill-dark: "rgba(255,255,255,.08)"
  section-haefen: "#0a8fa8"
  section-haefen-dark: "#5ac8de"
  section-kraene: "#e0a800"
  section-kraene-dark: "#ffd60a"
  section-industrie: "#f07800"
  section-industrie-dark: "#ff9f0a"
  section-tiefbau: "#a2845e"
  section-tiefbau-dark: "#c4a77d"
  section-markt: "#a64fd6"
  section-markt-dark: "#bf5af2"
  section-laender: "#f2305a"
  section-laender-dark: "#ff375f"
  section-rohstoffe: "#007aff"
  section-rohstoffe-dark: "#0a84ff"
  rating-green: "#34c759"
  rating-yellow: "#ff9f0a"
  rating-red: "#ff3b30"
typography:
  display:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Display, Inter, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "40px"
    fontWeight: 700
    lineHeight: 1.05
    letterSpacing: "-0.028em"
  figure:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Display, Inter, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "44px"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "-0.035em"
    fontFeature: "tnum"
  headline:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Display, Inter, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "34px"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.026em"
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Display, Inter, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "21px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.018em"
  item-title:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Display, Inter, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "17px"
    fontWeight: 600
    lineHeight: 1.38
    letterSpacing: "-0.018em"
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Text, Inter, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.47
    letterSpacing: "-0.011em"
  body-small:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Text, Inter, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Text, Inter, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.47
    letterSpacing: "-0.005em"
  pill:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Text, Inter, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "11px"
    fontWeight: 600
    letterSpacing: "0.01em"
rounded:
  focus: "6px"
  field: "10px"
  notice: "14px"
  card: "20px"
  capsule: "99px"
spacing:
  hair: "4px"
  row-gap: "14px"
  row: "16px"
  card-gap: "20px"
  card-x: "26px"
  gutter: "28px"
  gutter-phone: "18px"
  section: "40px"
  nav-after: "44px"
  group: "72px"
components:
  card:
    backgroundColor: "{colors.card}"
    rounded: "{rounded.card}"
  card-rows:
    backgroundColor: "{colors.card}"
    rounded: "{rounded.card}"
    padding: "6px 26px"
  list-row:
    padding: "16px 0"
  chart-card:
    backgroundColor: "{colors.card}"
    rounded: "{rounded.card}"
    padding: "24px 26px 14px"
  nav-segment:
    textColor: "{colors.secondary-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.capsule}"
    padding: "6px 13px"
  nav-segment-active:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.capsule}"
  pill-new:
    backgroundColor: "{colors.new-orange-wash}"
    textColor: "{colors.new-orange}"
    typography: "{typography.pill}"
    rounded: "{rounded.capsule}"
    padding: "2px 8px"
  pill-customer:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.card}"
    typography: "{typography.pill}"
    rounded: "{rounded.capsule}"
    padding: "2px 8px"
  disclosure-link:
    textColor: "{colors.system-blue}"
    rounded: "{rounded.focus}"
  rating-dot:
    rounded: "{rounded.capsule}"
    size: "16px"
  button-quiet:
    backgroundColor: "{colors.fill}"
    textColor: "{colors.ink}"
    rounded: "{rounded.capsule}"
    padding: "7px 14px"
  input-field:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    padding: "7px 12px"
---

# Design System: Rope Report

## Overview

**Creative North Star: "The Morning Keynote Page"**

The page reads like a classic Apple product page turned into a daily briefing: big, confident, tightly tracked headlines per group; white rounded surfaces floating on a soft grey ground; generous vertical air; nothing decorative. The density lives inside the cards, as calm list rows divided by inset hairlines in the manner of Apple's own apps, while the space between groups stays wide (72px). The only colour with intent is Apple system blue for anything you can act on, an orange capsule for "NEU", and a dark capsule for "Kunde"; section colours appear only as small dots next to their labels.

Light and dark follow the system setting. Light mode lifts cards off the ground with a barely-there two-layer shadow; dark mode drops shadows entirely and separates by tone (black ground, graphite cards). Type is SF Pro on Apple devices and embedded variable Inter (with optical sizes) everywhere else, so the page needs no external request. The world rejects the grey admin-dashboard look: bordered boxes, small grey uppercase kickers, badge clutter and icon decoration.

**Key Characteristics:**
- Soft grey ground, borderless white cards with a 20px radius, inset hairline rows.
- Large display headlines with negative tracking; tabular numerals on every figure, date and count.
- Translucent sticky bar (blurred, saturated) with segmented-control capsules for navigation.
- Blue is the action colour; section colours are dots, never fills.
- Text only: the rope cross-section mark is the sole graphic besides the charts.

## Colors

A near-monochrome Apple neutral palette with one action blue, one signal orange, and a quiet set of Apple system hues used as section dots.

### Primary
- **System Blue** (system-blue; dark: system-blue-dark): links on hover, the "Hintergrund" disclosure, focus rings, chart lines, area wash and points, text selection tint. It means "you can act here" and nothing else.

### Secondary
- **Signal Orange** (new-orange on new-orange-wash; dark: new-orange-dark on new-orange-wash-dark): only the "NEU" capsule. The light text tone is deepened to a burnt orange so the 11px label stays legible on its pale wash.
- **Rope Core Amber** (rope-core-amber): the core strand of the wire-rope mark and the sample-data banner. Constant across light and dark.

### Tertiary
- **Section dots** (section-haefen, section-kraene, section-industrie, section-tiefbau, section-markt, section-laender, section-rohstoffe, each with a brighter -dark variant): Apple system teal, yellow, orange, brown, purple, pink and blue. Each section owns one, always paired with its label, shown as a 7px dot in the navigation and a 9px dot before the section title.
- **Rating lights** (rating-green, rating-yellow, rating-red): the three outlined rating dots and the system-status dots. Same values in both modes.

### Neutral
- **Ground** (ground; dark: ground-dark): page background and the base of the translucent bar (78% mix).
- **Card** (card; dark: card-dark): every surface, and the text colour inside the "Kunde" capsule.
- **Ink** (ink; dark: ink-dark): headlines, item titles, body text, the rope mark's outer strands, the "Kunde" capsule fill.
- **Secondary Ink** (secondary-ink; dark: secondary-ink-dark): meta lines, countries, sources, dates in the masthead, inactive navigation. In light mode the faint tier uses this same value; in dark it steps down to faint-ink-dark for timestamps, chart axis labels and counts.
- **Hairline** (hairline; dark: hairline-dark): row dividers, chart grid, navigation bottom edge, footer rule, field stroke.
- **Fill** (fill; dark: fill-dark): resting background of quiet footer buttons.

### Named Rules
**The Blue Means Action Rule.** System blue appears only where the reader can click, focus or read a chart line. Never use it for emphasis or decoration.

**The Dot-And-Label Rule.** A section colour is only ever a small round dot (7–9px) beside its label. Never tint a card, a row, a headline or a border with it.

**The Two Pills Rule.** Only "NEU" and "Kunde" are capsules. Countries, sources, "Fachmedium" and source counts stay plain grey text.

## Typography

**Display Font:** SF Pro Display via the system stack (with embedded Inter, then Segoe UI, Roboto, Helvetica Neue, Arial)
**Body Font:** SF Pro Text via the system stack (with embedded Inter and the same fallbacks)

**Character:** One family in two optical cuts, exactly as Apple sets it: heavy, tightly tracked display lines over a quiet 17px text size. Inter's optical sizes (`font-optical-sizing:auto`) stand in for the Display/Text split off Apple hardware.

### Hierarchy
- **Display** (700, 40px, 1.05, -0.028em): the "Rope Report" masthead; the second word drops to secondary ink. 30px on phones.
- **Figure** (600, 44px, 1, -0.035em, tabular): the latest value on each chart card. 36px on phones.
- **Headline** (700, 34px, 1.1, -0.026em): group headings (Kennzahlen, Zielmärkte, Markt & Handel). 28px on phones.
- **Title** (600, 21px, 1.2, -0.018em): section titles with their colour dot.
- **Item Title** (600, 17px, 1.38, -0.018em): each news headline; chart titles use the same weight at 1.3. 16px on phones.
- **Body** (400, 17px, 1.47, -0.011em): base text. 16px on phones.
- **Body Small** (400, 15px, 1.5): the "Hintergrund" note, capped at 64ch; item text columns cap at 72ch.
- **Label** (400–500, 13px, -0.005em): meta lines, countries (500), masthead date/status, navigation (14px, 500), footer.
- **Pill** (600, 11px, +0.01em): "NEU" and "Kunde" only. Timestamps sit at 12px, chart axis text at 10.5px.

### Named Rules
**The Tabular Figures Rule.** Every number that can change from day to day (chart values, deltas, timestamps, navigation counts, the "Stand" line) uses tabular numerals so columns never jitter.

**The Tight Display Rule.** Tracking tightens as size grows: -0.011em at body, -0.018em at titles, -0.026em to -0.035em at headlines and figures. Small labels and pills stay at or above 0.

## Layout

A single centred column, max 1080px, with a 28px side gutter (18px at ≤600px). The masthead (mark, title, tagline left; date and "Stand" right) sits above a full-width sticky navigation bar; 44px below the bar the content begins. Groups are separated by 72px (52px on phones), sections by 40px.

The four target markets form a 2×2 grid of equal-height cards (36px row gap, 24px column gap) that collapses to one column at ≤600px. "Markt & Handel" sections stack full width. Chart cards sit two-up in a grid from 900px; below that they become a horizontally scrolling, snap-aligned strip with cards at min(86%, 420px) that bleeds to the screen edge.

Inside a list card, each row is a three-column grid: a 56px timestamp column, the text column, and the rating dots; rows are 16px top and bottom with a 14px gap. On phones the rating dots move under the text. Anchor jumps scroll smoothly with a 72px top offset to clear the sticky bar.

## Elevation & Depth

Hybrid, and mode-dependent. In light mode cards float on the grey ground with one ambient two-layer shadow; there are no borders on surfaces. In dark mode the shadow is removed and depth comes from tone alone (graphite card on black). The sticky navigation is a translucent material (ground at 78%, `saturate(180%) blur(20px)`) with a hairline bottom edge. The active navigation capsule carries its own small lift.

### Shadow Vocabulary
- **Card ambient** (`box-shadow: 0 1px 2px rgba(0,0,0,.04), 0 6px 20px rgba(0,0,0,.05)`): every card, chart card and the error notice, light mode only.
- **Segment lift** (`box-shadow: 0 1px 3px rgba(0,0,0,.08), 0 0 0 .5px var(--hair)`): the active navigation capsule, like the thumb of a segmented control.

### Named Rules
**The Flat Night Rule.** In dark mode nothing casts a shadow; cards separate by tone only.

**The No-Border Card Rule.** Surfaces are defined by fill and shadow, never by an outline. Hairlines divide rows inside a card, not cards from the page (print is the one exception, where shadows become a 1px border).

## Shapes

Soft, continuous rounding. Cards use a generous 20px radius and clip their contents; the error notice uses 14px; the token field 10px; focus rings and disclosure summaries 6px. Everything interactive and small is a full capsule (99px): navigation segments, pills, footer buttons. Dots are perfect circles: 7px navigation dots, 9px section dots, 8px status dots, 16px rating dots (18px on phones, with an enlarged invisible hit area). Disclosure chevrons are drawn as a rotated two-sided border, not a glyph.

## Components

### Navigation
Translucent segmented-control bar. Each link is a 14px/500 secondary-ink capsule (6px 13px) led by its section dot and followed by a 12px tabular count; hover turns it to ink. The section in view becomes the active segment: card fill, ink text, segment lift. A thin vertical hairline separates "Kennzahlen" from the news sections. On narrow screens the bar scrolls horizontally without a scrollbar and auto-centres the active segment. Transitions run 0.2s on background, colour and shadow.

### Cards / Containers
- **Corner Style:** 20px.
- **Background:** card.
- **Shadow Strategy:** card ambient in light, none in dark.
- **Border:** none.
- **Internal Padding:** list cards 6px 26px (4px 18px on phones), rows inside 16px 0; chart cards 24px 26px 14px; empty state 20px 26px in 15px faint text.

### List Row (signature)
Timestamp column in 12px faint tabular text; then an optional meta line (countries in 500 grey, then the pills), the item title in ink (blue on hover), a meta line with the source, and the "Hintergrund" disclosure. Rows are divided by full-width hairlines inside the card's padding, so they read inset; the first row has none.

### Chips
- **NEU:** signal-orange text on its orange wash, 11px/600 capsule, 2px 8px.
- **Kunde:** card-coloured text on an ink capsule, same metrics; inverts naturally in dark mode.

### Disclosure ("Hintergrund")
A 14px/500 blue text link with a small chevron that rotates from down to up over 0.2s; underline on hover with a 3px offset. Opens a 15px note (max 64ch) and a row of 12.5px grey source links that turn blue on hover.

### Rating Dots
Three 16px outlined circles (green, yellow, red, red set 6px apart), 1.6px stroke at 70% opacity, rising to 90% when the row is hovered or focused and 100% with a 1.12 scale on direct hover. A selected rating fills its circle. A red rating collapses the row to a 14px "Rückgängig" line with a blue text button.

### Chart Card
Title (17px/600) and grey subtitle left, the 44px figure and its period right; a line of bold tabular deltas with grey qualifiers; an SVG line chart with a 2.2px rounded blue line, an 8% blue area wash, blue points ringed in the card colour, and hairline grid; a 11.5px faint footer with a blue source link.

### Buttons and Inputs
- **Quiet button:** 13px/500 ink text on the fill tint, capsule, 7px 14px; hover deepens the tint to 12% ink.
- **Text button:** 14px/500 system blue, no background, underline on hover.
- **Input field:** 14px text, 7px 12px, hairline stroke, 10px radius, card background; full width on phones.
- **Focus:** a 2px system-blue outline offset 3px with a 6px radius on every focusable element (circular on rating dots).

### Status Line
A collapsible grey 13px summary led by an 8px status dot (green, amber or red), opening to a plain list of checks. A red state also shows a full-width banner at the very top: 13px ink on a 12% red mix of the card colour.

## Do's and Don'ts

### Do:
- **Do** put every surface on the card token with the 20px radius and the card ambient shadow, and let dark mode drop the shadow.
- **Do** separate rows with inset hairlines inside the card, never with gaps between separate boxes.
- **Do** use system blue for every link, disclosure, focus ring and chart line, and for nothing else.
- **Do** show a section's colour as a 7–9px dot beside its label.
- **Do** set headlines heavy and tightly tracked (-0.026em at 34px) and every changing number in tabular figures.
- **Do** keep 72px between groups and 40px between sections; the air is part of the style.

### Don't:
- **Don't** draw borders around cards or fill cards, rows or headings with a section colour.
- **Don't** add capsules beyond "NEU" and "Kunde"; countries and sources stay grey text.
- **Don't** use small grey uppercase kickers or eyebrows above headings.
- **Don't** add shadows in dark mode.
- **Don't** add icons, photos or decorative graphics; the rope mark and the charts are the only images.
- **Don't** load fonts or anything else from outside the page; Inter is embedded, SF Pro comes from the device.
