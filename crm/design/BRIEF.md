# Book Factory CRM - design brief

Phase 21. The agreed look for the CRM: one place to see the books, their KDP
sales and the ideas board, on Kieran's phone and laptop. The exact values are
in `tokens.json`; the clickable mockup is `crm/mockup/index.html`.

## The idea

The CRM should look like it comes from the same shop as the books. It borrows
their parts, not a generic dashboard template:

- **Big condensed lettering** (Anton) from the Golf and Padel covers, used
  only for headings and the big numbers.
- **The Runner's "stats panel"**: a near-black panel with lime figures in a
  monospaced face, as on the Runner's cover. It is used once per screen, for
  the numbers that matter most. This is the one bold element; everything
  around it stays quiet.
- **The books' own paper** as the page background, and each book keeps its
  cover colour (Golf green, Padel navy, Runner's orange) wherever it appears:
  the spine stripe on its card, its bars in the sales charts, its dot in
  lists.
- **Real covers** are the main pictures. No stock images, no icons as
  decoration.

## Colours

| Token | Light | Dark | Used for |
| --- | --- | --- | --- |
| `paper` | `#F4F2EB` | `#131311` | page background |
| `sheet` | `#FCFBF7` | `#1C1B18` | cards and panels |
| `ink` | `#17150F` | `#F1EEE5` | text |
| `ink-soft` | `#5E5A50` | `#A9A496` | secondary text |
| `rule` | `#DDD8CB` | `#2F2D28` | hairlines |
| `panel` | `#17150F` | `#0B0B0A` | the stats panel |
| `lime` | `#C8F03C` | `#C8F03C` | figures on the stats panel only |
| `accent` | `#E4572E` | `#F2764F` | the one action colour: active tab, main button |

Book colours: Golf `#1D5C36`, Padel `#1F3A66`, Runner's `#FF5A1F` (lighter
versions in dark mode). Status colours are separate from the accent: good
`#2F7D4F`, waiting `#B7800E`, problem `#C23B2A`.

## Type

- **Anton**: headings and big numbers, uppercase, never for running text.
- **Archivo**: everything else (the covers' own body face).
- **JetBrains Mono**: figures, dates, small labels (like the Runner's stats
  panel), always with lined-up digits.

## Shape and motion

- Spacing on a 4px grid: 4, 8, 12, 16, 24, 32, 48.
- Corners: 6px on cards, 999px on status pills, 2px on covers (like a real
  book).
- Hairline borders instead of shadows. Only a dragged card gets a shadow.
- Movement is short (160ms, eased out) and switched off for anyone who has
  "reduce motion" set on their device.

## Layout

- **Laptop**: a narrow left column for navigation, content up to 1200px wide.
- **Phone**: a tab bar at the bottom, one column, the ideas board scrolls
  sideways one column at a time.
- Four screens: **Home**, **Shelf**, **Sales**, **Ideas**.

## Rules

- Sample numbers are always labelled "Sample" until Kieran's KDP report is
  imported. Never show made-up figures as real.
- Book stages and next steps come from the repository (`bookfactory status`),
  never typed in by hand.
