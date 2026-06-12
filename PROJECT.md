# Project: SNA Dashboard

## Overview
Dashboard visual penjualan PT Saka Niaga Sukses Abadi (SNA). Menggabungkan data sales 2025-2026, stock inventory, dan supply chain planning. Target user: Ery Wirawan (owner) untuk monitoring bisnis building material distributor di Bali + 5 region.

**Status:** 🟡 Active Development
**Started:** 2026-06-12

## Tech Stack
- HTML + CSS (dark theme, Chart.js for visualization)
- Python (data processing, fetch from Google Sheets)
- Vercel (hosting)

## Directory Structure
```
/root/sna-dashboard/
├── PROJECT.md          # This file
├── index.html          # Dashboard utama (Chart.js, self-contained)
├── chart.min.js        # Chart.js v4.4.0 (local, bukan CDN)
├── fetch_data.py       # Script fetch + clean data dari Google Sheets
├── deploy.sh           # Deploy manual ke Vercel
└── refresh-and-deploy.sh  # Full refresh data + rebuild + deploy
```

## Data Sources (Google Sheets Published)
| Data | Spreadsheet ID | GID | Rows | Status |
|------|---------------|-----|------|--------|
| Master Supplier | `2PACX-1vSplC2GmI4l5uS-8TvtPsKM2rn14mXn-eOMrA-NQ7fi6fdJIh_MFNgXZf9xzBrHcVRhAD_GNeF7M0FG` | - | 35 suppliers | ✅ |
| Master Items | same | - | 556 SKUs | ✅ |
| Sales 2025 | `2PACX-1vQRMd7QV5MC2cCOjgI0rpEh3-Pu5O7xUTuXxBwuTaix3TsnRuzv6-sGsSg2PiL1IxFy-NJHn3TqGWEG` | `1433429075` | 93,022 rows | ✅ |
| Sales 2026 YTD | `2PACX-1vRvkbsWaEZy4yoGxkhszQVeaoQ0CSPqeJJpdSiQAnkc-4TtoC51-KXTMD-4W80Gdly5LNmKs5fd8-Ez` | `1613807729` | 34,656 rows | ✅ |
| Stock List Non Semen | `2PACX-1vRRcU8w42A6Go3p8DqMycMEeFFy43COjIsC0W7yLpnWkjN_YyJgrQ2vyJHz3q7QJUdtxnq2rYFCFls7` | - | 4,226 items | ✅ |
| *Tambahan* | *menunggu* | - | - | ⏳ |

## Credentials & Config
| Item | Location | Notes |
|------|----------|-------|
| Vercel Token | `~/.hermes/secrets/vercel_token` | Deploy ke Vercel |
| GitHub Token | User paste di chat | `ghp_zN...d7ZP`, repo: `erywiirawan/sna-dashboard` |

## Deploy / Run
| Action | Command |
|--------|---------|
| Deploy manual | `bash /root/sna-dashboard/deploy.sh` |
| Refresh data + deploy | `bash /root/sna-dashboard/refresh-and-deploy.sh` |
| Fetch data only | `python3 /root/sna-dashboard/fetch_data.py` |

## Key Metrics (per 12 Jun 2026)
- Revenue 2025: Rp 182.4B (full year)
- Revenue 2026 YTD: Rp 78.1B (4 bln), annualized Rp 234.2B (+28.4% YoY)
- 24 cabang, 3,617 pelanggan, 1,292 SKU, 69,059 invoices
- Stock: 4,226 items, 17 cabang, 94 gudang, 1,381 SKU unik

## Key Decisions & Gotchas
- Chart.js local (bukan CDN): browserbase gak bisa load CDN di file:// protocol
- Indonesian number format: `.` = thousands, `,` = decimal → parse: `replace('.','').replace(',','.')`
- CSV quoting issue: Google Sheets export punya embedded commas → pakai Python csv module, bukan awk
- `sna-dashboard-rouge.vercel.app` = production URL (auto-alias)

## Roadmap
- [x] Sales dashboard (2025+2026)
- [x] Deploy ke Vercel
- [ ] Tab Stock vs Sales (slow-moving, overstock, stockout risk)
- [ ] Tab Inventory Movement (IN/OUT per branch, turnover)
- [ ] Tab Supply Planning (reorder suggestion)
- [ ] Gabung semua data sources

## Change Log
| Date | Change |
|------|--------|
| 2026-06-12 | Initial: sales dashboard + deploy ke Vercel |
| 2026-06-12 | Added stock data source (non-cement, 4,226 items) |
| 2026-06-12 | Created PROJECT.md |
