---
version: alpha
name: SNA Dashboard
description: Dark-themed business intelligence dashboard for PT Saka Niaga Abadi — a building material distributor. Optimized for data density, quick scanning, and professional monitoring.

colors:
  bg: "#0f1117"
  card: "#1a1d29"
  border: "#2a2d3a"
  text: "#e0e0e0"
  dim: "#8888aa"
  accent: "#6c5ce7"
  accent2: "#00cec9"
  green: "#00b894"
  red: "#e17055"
  orange: "#fdcb6e"
  blue: "#74b9ff"
  purple: "#a29bfe"
  header-from: "#1a1d29"
  header-to: "#2d1f3d"

typography:
  h1:
    fontFamily: "'Segoe UI', system-ui, sans-serif"
    fontSize: "20px"
    fontWeight: 700
    lineHeight: 1.2
  h3:
    fontFamily: "'Segoe UI', system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0.02em"
  body:
    fontFamily: "'Segoe UI', system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "'Segoe UI', system-ui, sans-serif"
    fontSize: "11px"
    fontWeight: 400
    lineHeight: 1.3
    letterSpacing: "0.05em"
  value-lg:
    fontFamily: "'Segoe UI', system-ui, sans-serif"
    fontSize: "22px"
    fontWeight: 700
    lineHeight: 1.2
  value-md:
    fontFamily: "'Segoe UI', system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 600
    lineHeight: 1.2

rounded:
  sm: "6px"
  md: "8px"
  lg: "12px"
  xl: "16px"

spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"

components:
  header:
    background: "linear-gradient(135deg, {colors.header-from}, {colors.header-to})"
    padding: "16px 24px"
    textColor: "#ffffff"
  card:
    backgroundColor: "{colors.card}"
    borderColor: "{colors.border}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
  kpi-card:
    backgroundColor: "{colors.bg}"
    borderColor: "{colors.border}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#ffffff"
    rounded: "{rounded.sm}"
    padding: "6px 16px"
  button-reset:
    backgroundColor: "transparent"
    textColor: "{colors.dim}"
    borderColor: "{colors.border}"
    rounded: "{rounded.sm}"
    padding: "6px 16px"
  filter-select:
    backgroundColor: "{colors.bg}"
    textColor: "{colors.text}"
    borderColor: "{colors.border}"
    rounded: "{rounded.sm}"
    padding: "6px 10px"
  tab-active:
    textColor: "{colors.accent}"
    borderColor: "{colors.accent}"
  tab-inactive:
    textColor: "{colors.dim}"
    borderColor: "transparent"
  modal:
    backgroundColor: "{colors.card}"
    borderColor: "{colors.border}"
    rounded: "{rounded.md}"
  table-header:
    textColor: "{colors.dim}"
    borderColor: "{colors.border}"
  status-good:
    backgroundColor: "{colors.green}"
  status-warn:
    backgroundColor: "{colors.orange}"
  status-bad:
    backgroundColor: "{colors.red}"
---

## Overview

The SNA Dashboard is a dark-themed business intelligence tool for monitoring sales, inventory, procurement, and supply chain metrics of PT Saka Niaga Abadi — a building material distributor operating across 24 branches in Indonesia.

The design prioritizes **data density** and **quick scanning**. The dark palette reduces eye strain during extended monitoring sessions. High-contrast accent colors draw attention to key metrics, trends, and actionable data points.

## Colors

The palette uses a deep navy-charcoal foundation with vibrant accent colors for data visualization:

- **Background (#0f1117):** Deep space — the canvas. Almost-black with a slight blue undertone, softer than pure #000.
- **Card (#1a1d29):** Elevated surface — slightly lighter than background, creating depth through layering.
- **Border (#2a2d3a):** Subtle separators — low-contrast borders that define structure without visual noise.
- **Text (#e0e0e0):** Primary content — high contrast against dark backgrounds for readability.
- **Dim (#8888aa):** Secondary text — labels, captions, metadata. Muted but still legible.
- **Accent (#6c5ce7):** Primary action — purple for interactive elements, active tabs, primary buttons.
- **Accent2 (#00cec9):** Teal for 2026 data in charts, growth indicators, positive trends.
- **Green (#00b894):** Success — positive growth, healthy metrics, good status.
- **Red (#e17055):** Alert — negative growth, low stock, critical status.
- **Orange (#fdcb6e):** Warning — moderate alerts, watch status.
- **Blue (#74b9ff):** Information — supplementary data, 2025 chart bars.

### Data Color Semantics

| Context | Color | Token |
|---------|-------|-------|
| 2025 data (charts) | Blue/Purple | `{colors.accent}` at 40% opacity |
| 2026 data (charts) | Teal | `{colors.accent2}` at 50% opacity |
| Positive YoY growth | Green | `{colors.green}` |
| Negative YoY growth | Red | `{colors.red}` |
| Filter active badge | Purple | `{colors.accent}` |

## Typography

A single font family (`Segoe UI` / system-ui) at small sizes (11-13px) keeps the interface compact and data-dense. Larger sizes (18-22px) are reserved for KPI values.

- **Labels (11px, uppercase, 0.05em spacing):** Filter labels, table headers, KPI card labels. Creates visual hierarchy without bold weight.
- **Body (13px):** Default for all content — tables, charts, filter options. Small enough for density, large enough for readability.
- **Values (18-22px, bold):** KPI card numbers. The only large text on screen — draws the eye to key metrics.

## Layout

The layout uses a single-page vertical stack:

1. **Header** — Logo, title, subtitle
2. **Filter bar** — Horizontal row of dropdowns + action buttons
3. **Tab bar** — Penjualan, Stok, Pengadaan, Supply Chain
4. **KPI bar** — 4-column grid of metric cards
5. **Charts** — 2-column grid (monthly + branch chart)
6. **Details** — 2-column grid (products + LOB chart)
7. **Tables** — Full-width item and customer tables

All content uses `padding: 12px 24px` for consistent horizontal rhythm.

## Shapes

- **Cards:** 8px rounded corners — soft enough to feel modern, sharp enough for data density.
- **Buttons:** 6px rounded corners — slightly tighter than cards.
- **Badges/Tags:** 12px rounded corners (pill-like) for filter badges.
- **No shadows** — depth is created through background color layering, not elevation.

## Components

### KPI Card

The primary metric display. Shows a label, main value, and optional sub-value.

- Background is `{colors.bg}` (darker than card) to create contrast
- Label is uppercase `{colors.dim}` at 10px
- Value is white at 18-22px bold
- Sub-value is `{colors.green}` for positive trends

### Chart

Chart.js visualizations with dark theme:

- Grid lines use `{colors.border}` at low opacity
- Legend text uses `{colors.dim}`
- Tooltips use `{colors.card}` background
- Y-axis labels use `{colors.dim}` with abbreviated format (K, M, B)

### Modal

Overlay for drill-down details:

- Background overlay: black at 50% opacity
- Content: `{colors.card}` with `{colors.border}` border
- Close button: `{colors.dim}`, hover to `{colors.red}`
- Table inside modal follows same table styling

## Do's and Don'tts

### Do
- Use abbreviated number format: K (ribu), M (juta), B (miliar)
- Show year-specific data when year filter is active
- Keep filter state visible (badge count)
- Use color semantics consistently (green=good, red=bad, teal=2026)

### Don't
- Don't use pure white (#fff) for body text — use `{colors.text}` (#e0e0e0)
- Don't add shadows — use background layering for depth
- Don't exceed 13px for body text — data density is paramount
- Don't use more than 3 accent colors in a single chart
