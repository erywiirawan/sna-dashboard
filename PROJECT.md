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
├── index.html          # Dashboard utama (Chart.js, self-contained, ~3.6MB embedded JSON)
├── chart.min.js        # Chart.js v4.4.0 (local, bukan CDN)
├── fetch_data.py       # Script fetch + clean data dari Google Sheets → dashboard_data.json
├── build_dashboard.py  # Embed dashboard_data.json ke index.html
├── dashboard_data.json # Generated data file (~4MB)
├── deploy.sh           # Rebuild + deploy ke Vercel
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
| Procurement PO | `2PACX-1vTOO_1ht5wm1C8M979gNSgkJI3BM-wuuxxJTmjviNHXyCfaZpfcWz2sN3BdetmEAiRuczUIC1pF8nGZ` | `1218677320` | 5,302 rows | ✅ |
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
- `build_dashboard.py` harus dijalankan SETIAP kali `fetch_data.py` atau `index.html` JS diubah
- `getActiveFilters()` return `{branches[], months, supplier, years}` — `branches` multi-select array, `supplier` singular string
- Cache structure: `branch_cache` (per-branch), `month_cache` (per-month), `branch_month_cache` (per-branch-per-month), `supplier_cache` (per-supplier), `supplier_branch_sp` (per-supplier-per-branch salesperson), `supplier_branch_cache` (per-supplier-per-branch full aggregation: monthly, products, SKU, items, customers, LOB)
- `supplier_branch_sp` key format: `supplier_name` → per-branch salesperson data, `supplier_name_months` → per-branch-month salesperson data

## Roadmap
- [x] Sales dashboard (2025+2026)
- [x] Deploy ke Vercel
- [x] Tab Stock (stock per branch, stock vs sales velocity)
- [x] Tab Procurement (PO pipeline, supplier performance)
- [x] Tab Supply Chain Overview (cross-reference)
- [x] Global filter: Branch (multi-select), Month, Year (multi-select), Supplier
- [x] Year filter: multi-select checkbox dropdown, YoY growth logic
- [x] Branch filter: multi-select checkbox dropdown, mergeBranchCaches()
- [x] Total SKU accuracy: per-cabang-per-bulan-per-tahun counting
- [x] KPI: Revenue, YoY Growth, SKU, Top Group Item (4-column grid)
- [x] Salesperson detail modal on branch bar click (year-aware)
- [x] Supplier filter → Sales tab (branch_monthly + supplier_branch_sp for modal)
- [x] Group Name display (Top Group Item card + Top 10 Produk chart)
- [x] Top Group Item clickable → Class Name detail modal (year-aware)
- [x] Year filter → Products/Group/Class breakdown (values25/26, classes25/26)
- [ ] Auto-refresh data dari Google Sheets

## Change Log
| Date | Change |
|------|--------|
| 2026-06-12 | Initial: sales dashboard + deploy ke Vercel |
| 2026-06-12 | Added stock data source (non-cement, 4,226 items) |
| 2026-06-12 | Created PROJECT.md |
| 2026-06-12 | Built 4-tab dashboard: Sales + Stock + Procurement + Supply Chain |
| 2026-06-12 | Added global filter bar: Branch, Month, Supplier + pre-computed caches |
| 2026-06-13 | Added year filter (multi-select checkbox), YoY growth logic |
| 2026-06-13 | Fixed Total SKU accuracy (per-branch-per-month-per-year counting) |
| 2026-06-13 | Added build_dashboard.py (embed JSON into HTML) |
| 2026-06-13 | KPI row: 4-column (Revenue, YoY, SKU, Top Group Item) |
| 2026-06-13 | Salesperson detail modal on branch click (year-aware, per-branch-per-month) |
| 2026-06-13 | Supplier filter affects Sales tab: branch_monthly + supplier_branch_sp |
| 2026-06-13 | Supplier filter affects salesperson modal (supplier_branch_sp cache) |
| 2026-06-13 | Group Name display: group_name_map + class_name_map in data |
| 2026-06-13 | Top Group Item clickable → Class Name detail modal |
| 2026-06-13 | Year filter → Products/Group/Class breakdown (values25/26, classes25/26) |
| 2026-06-19 | Fix: branch+supplier filter — added `supplier_branch_cache` for per-cabang data |
| 2026-06-19 | Feat: branch filter multi-select (checkbox dropdown, same pattern as month/year) |
| 2026-06-19 | Added `mergeBranchCaches()` + `mergeSupplierBranchCaches()` JS functions |
| 2026-06-19 | Fix: `.branch-container` CSS `position:relative` for dropdown positioning |
| 2026-06-19 | Fix: Top 20 Items empty when supplier+branch+month — fallback to supplier_branch_cache items |
| 2026-06-19 | Fix: Customer revenue now supplier-specific (supplier_br_month_cust cache) |
| 2026-06-19 | Format: Revenue values use K/M/B without Rp prefix (fmt() not fmtRp()) |
| 2026-06-19 | Feat: precise per-month-per-branch items for supplier filter (`_br_month_items` cache) |
