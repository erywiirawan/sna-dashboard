import csv, io, json, os
from collections import Counter, defaultdict
from datetime import datetime

MASTER_ITEMS = '/root/master_list_items.csv'
MASTER_SUPPLIERS = '/root/master_supplier_list.csv'
SALES_2025 = '/tmp/sheet_a.csv'
SALES_2026 = '/tmp/sheet_b.csv'

# Load Master Items
master_items = {}
with open(MASTER_ITEMS, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        kode = (row.get('Kode') or '').strip()
        if kode:
            master_items[kode] = {
                'nama': (row.get('Nama Barang') or '').strip(),
                'satuan': (row.get('Satuan') or '').strip().upper(),
                'group': (row.get('Group') or '').strip(),
                'class': (row.get('Class') or '').strip(),
                'type': (row.get('Type') or '').strip(),
                'supplier': (row.get('SUPPLIER') or '').strip(),
            }
print(f"Master Items loaded: {len(master_items)}")

GRUP_NAMES = {
    '01TRP': 'Triplek', '02GRC': 'GRC Board', '03PKU': 'Paku',
    '04KB': 'Kawat Bendrat', '05SGG': 'Seng Gelombang', '05TLG': 'Talang Galvalum',
    '06HL': 'Hollow', '08TRMK': 'Triplek MRK/PLY', '08SPDK': 'Spandek',
    '10PMP': 'Pipa PVC', '10PGLW': 'Pipa Galvanis', '14WRM': 'Wiremesh',
    '15BJR': 'Baja Ringan', '16BL': 'Batu Alam/Bata', '19LMR': 'Lemari/Meja Rak',
    '19LMF': 'Lem Fox', '19LEM': 'Lem', '20DJ': 'Djabesmen/Seng DJ',
    '21KR': 'Karpet/Tikar', '22KS': 'Kusen/Alumunium', '28GPSM': 'Gypsum',
    '30KBL': 'Kabel', '33IDSR': 'Eco Board', '34HMWR': 'Hardware',
    '35ASPL': 'Aspal',
}

def parse_sales(filepath):
    rows = []
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        header = None
        for row in reader:
            if not header:
                if row and row[0] == 'No':
                    header = row
                continue
            if len(row) < 14:
                continue
            
            cabang = row[1].strip()
            tanggal = row[2].strip()
            kode_pel = row[3].strip()
            pelanggan = row[4].strip().replace('"', '')
            nomor = row[5].strip()
            grup_item = row[6].strip()
            item = row[7].strip()
            
            def pf(s):
                try: return float(s.replace(',','').replace('"','').strip())
                except: return 0
            
            qty = pf(row[8])
            harga = pf(row[9])
            diskon = pf(row[10])
            jumlah = pf(row[11])
            total = pf(row[12])
            
            status = row[13].strip() if len(row) > 13 else ''
            sales_code = row[14].strip() if len(row) > 14 else ''
            sf_user = row[15].strip() if len(row) > 15 else ''
            area = row[16].strip() if len(row) > 16 else ''
            lob = row[17].strip() if len(row) > 17 else ''
            delivery = row[19].strip() if len(row) > 19 else ''
            keterangan = row[20].strip() if len(row) > 20 else ''
            to_p = row[23].strip() if len(row) > 23 else ''
            
            try:
                dt = datetime.strptime(tanggal, '%d-%b-%y')
                bulan = dt.strftime('%b')
                tahun = dt.year
            except:
                bulan = ''
                tahun = 0
            
            grup_nama = GRUP_NAMES.get(grup_item, grup_item)
            master = master_items.get(item, {})
            supplier = master.get('supplier', '')
            
            rows.append({
                'tahun': tahun, 'bulan': bulan, 'tanggal': tanggal,
                'cabang': cabang, 'kode_pelanggan': kode_pel,
                'pelanggan': pelanggan, 'nomor_invoice': nomor,
                'grup_item': grup_item, 'grup_nama': grup_nama,
                'item': item, 'keterangan': keterangan,
                'qty': qty, 'harga': harga, 'diskon': diskon,
                'jumlah': jumlah, 'total_invoice': total,
                'status': status, 'sales': sales_code, 'sf_user': sf_user,
                'area': area, 'lob': lob, 'delivery': delivery,
                'to_p': to_p, 'supplier': supplier,
            })
    return rows

print("\nLoading Sheet A (2025)...")
sales_2025 = parse_sales(SALES_2025)
print(f"  Parsed: {len(sales_2025):,} rows")

print("Loading Sheet B (2026)...")
sales_2026 = parse_sales(SALES_2026)
print(f"  Parsed: {len(sales_2026):,} rows")

all_sales = sales_2025 + sales_2026
print(f"\nTotal combined: {len(all_sales):,} rows")

# Save cleaned CSV
clean_path = '/root/sna_sales_clean.csv'
fields = ['tahun','bulan','tanggal','cabang','kode_pelanggan','pelanggan',
          'nomor_invoice','grup_item','grup_nama','item','keterangan',
          'qty','harga','diskon','jumlah','total_invoice','status',
          'sales','sf_user','area','lob','delivery','to_p','supplier']

with open(clean_path, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(all_sales)
print(f"\nCleaned CSV saved: {clean_path}")

# ============================================================
# ANALYSIS
# ============================================================

print("\n" + "="*70)
print("DEEP ANALYSIS - PT SAKA NIAGASUKSE ABADI (SNA)")
print("="*70)

total_revenue = sum(r['jumlah'] for r in all_sales)
total_lines = len(all_sales)
unique_customers = len(set(r['kode_pelanggan'] for r in all_sales if r['kode_pelanggan']))
unique_items = len(set(r['item'] for r in all_sales))
unique_invoices = len(set(r['nomor_invoice'] for r in all_sales))
unique_branches = len(set(r['cabang'] for r in all_sales))

print(f"\nOVERALL STATS (2025 + 2026 YTD)")
print(f"  Total Revenue: Rp {total_revenue:,.0f}")
print(f"  Total Line Items: {total_lines:,}")
print(f"  Total Invoices: {unique_invoices:,}")
print(f"  Unique Customers: {unique_customers:,}")
print(f"  Unique SKUs: {unique_items:,}")
print(f"  Active Branches: {unique_branches}")

# Year comparison
rev_2025 = sum(r['jumlah'] for r in sales_2025)
rev_2026 = sum(r['jumlah'] for r in sales_2026)
lines_2025 = len(sales_2025)
lines_2026 = len(sales_2026)
inv_2025 = len(set(r['nomor_invoice'] for r in sales_2025))
inv_2026 = len(set(r['nomor_invoice'] for r in sales_2026))

months_2026 = sorted(set((r['bulan'], r['tahun']) for r in sales_2026 if r['tahun']==2026))
n_months_2026 = max(len(months_2026), 1)
rev_2026_ann = rev_2026 / n_months_2026 * 12

print(f"\n2026 Data Months: {n_months_2026}")

print(f"\nYoY COMPARISON")
print(f"  Revenue 2025: Rp {rev_2025:,.0f}")
print(f"  Revenue 2026 YTD ({n_months_2026}mo): Rp {rev_2026:,.0f}")
print(f"  Revenue 2026 Annualized: Rp {rev_2026_ann:,.0f}")
print(f"  Growth: {((rev_2026_ann/rev_2025)-1)*100:+.1f}%")

# Monthly trend 2025
month_order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
monthly_2025 = defaultdict(float)
for r in sales_2025:
    if r['tahun'] == 2025:
        monthly_2025[r['bulan']] += r['jumlah']

print(f"\nMONTHLY REVENUE 2025:")
for m in month_order:
    val = monthly_2025.get(m, 0)
    bar = '#' * max(1, int(val / 2_000_000_000))
    print(f"  {m}: Rp {val/1e9:>7.1f}M {bar}")

monthly_2026 = defaultdict(float)
for r in sales_2026:
    if r['tahun'] == 2026:
        monthly_2026[r['bulan']] += r['jumlah']

print(f"\nMONTHLY REVENUE 2026:")
for m in month_order:
    val = monthly_2026.get(m, 0)
    if val > 0:
        bar = '#' * max(1, int(val / 2_000_000_000))
        print(f"  {m}: Rp {val/1e9:>7.1f}M {bar}")

# Branch performance
branch_rev_2025 = defaultdict(float)
branch_lines_2025 = defaultdict(int)
for r in sales_2025:
    branch_rev_2025[r['cabang']] += r['jumlah']
    branch_lines_2025[r['cabang']] += 1

branch_rev_2026 = defaultdict(float)
branch_lines_2026 = defaultdict(int)
for r in sales_2026:
    branch_rev_2026[r['cabang']] += r['jumlah']
    branch_lines_2026[r['cabang']] += 1

print(f"\nBRANCH PERFORMANCE:")
for cabang in sorted(branch_rev_2025.keys(), key=lambda x: branch_rev_2025[x], reverse=True):
    r25 = branch_rev_2025[cabang]
    r26 = branch_rev_2026.get(cabang, 0)
    l25 = branch_lines_2025[cabang]
    l26 = branch_lines_2026.get(cabang, 0)
    ann = r26 / n_months_2026 * 12 if n_months_2026 else 0
    growth = ((ann/r25)-1)*100 if r25 > 0 else 0
    share = r25/rev_2025*100
    print(f"  {cabang:<8} 25: Rp {r25/1e9:>7.1f}M ({share:>4.1f}%) | 26YTD: Rp {r26/1e9:>7.1f}M | Growth: {growth:>+6.1f}%")

# Product group
grup_rev = defaultdict(float)
grup_qty = defaultdict(float)
grup_lines = defaultdict(int)
for r in all_sales:
    g = r['grup_item']
    grup_rev[g] += r['jumlah']
    grup_qty[g] += r['qty']
    grup_lines[g] += 1

print(f"\nPRODUCT GROUP PERFORMANCE:")
for g in sorted(grup_rev.keys(), key=lambda x: grup_rev[x], reverse=True):
    name = GRUP_NAMES.get(g, g)[:18]
    pct = grup_rev[g]/total_revenue*100
    avg_price = grup_rev[g]/grup_qty[g] if grup_qty[g] else 0
    print(f"  {g:<10} {name:<18} Rp {grup_rev[g]/1e9:>8.1f}M ({pct:>4.1f}%) Qty:{grup_qty[g]:>10,.0f} Avg:Rp {avg_price:,.0f}")

# Top items
item_rev = defaultdict(float)
item_qty = defaultdict(float)
item_name = {}
for r in all_sales:
    item_rev[r['item']] += r['jumlah']
    item_qty[r['item']] += r['qty']
    if r['keterangan']:
        item_name[r['item']] = r['keterangan']

print(f"\nTOP 20 ITEMS BY REVENUE:")
for item in sorted(item_rev.keys(), key=lambda x: item_rev[x], reverse=True)[:20]:
    name = item_name.get(item, '')[:40]
    pct = item_rev[item]/total_revenue*100
    print(f"  {item:<25} {name:<40} Rp {item_rev[item]/1e9:>7.2f}M ({pct:>3.1f}%) Qty:{item_qty[item]:>8,.0f}")

# Top customers + Pareto
cust_rev = defaultdict(float)
cust_name = {}
cust_cabang = {}
for r in all_sales:
    k = r['kode_pelanggan']
    if k:
        cust_rev[k] += r['jumlah']
        cust_name[k] = r['pelanggan']
        cust_cabang[k] = r['cabang']

sorted_custs = sorted(cust_rev.keys(), key=lambda x: cust_rev[x], reverse=True)
total_cust_rev = sum(cust_rev.values())
cumulative = 0
pareto_80 = None
pareto_50 = None

print(f"\nTOP 20 CUSTOMERS BY REVENUE:")
for i, k in enumerate(sorted_custs[:20]):
    cumulative += cust_rev[k]
    cum_pct = cumulative / total_cust_rev * 100
    name = cust_name.get(k, '')[:28]
    cab = cust_cabang.get(k, '')
    print(f"  {k:<16} {name:<28} {cab:<5} Rp {cust_rev[k]/1e9:>7.2f}M Cum:{cum_pct:>5.1f}%")

cumulative = 0
for i, k in enumerate(sorted_custs):
    cumulative += cust_rev[k]
    if not pareto_50 and cumulative >= total_cust_rev * 0.5:
        pareto_50 = i + 1
    if not pareto_80 and cumulative >= total_cust_rev * 0.8:
        pareto_80 = i + 1
        break

print(f"\nPareto: Top {pareto_50} cust ({pareto_50/len(sorted_custs)*100:.1f}%) = 50% rev")
print(f"Pareto: Top {pareto_80} cust ({pareto_80/len(sorted_custs)*100:.1f}%) = 80% rev")
print(f"Total unique customers: {len(sorted_custs):,}")

# LOB
lob_rev = defaultdict(float)
lob_lines = defaultdict(int)
for r in all_sales:
    lob_rev[r['lob']] += r['jumlah']
    lob_lines[r['lob']] += 1

print(f"\nLINE OF BUSINESS:")
for lob in sorted(lob_rev.keys(), key=lambda x: lob_rev[x], reverse=True):
    pct = lob_rev[lob]/total_revenue*100
    print(f"  {lob:<10} Rp {lob_rev[lob]/1e9:>10.1f}M ({pct:>5.1f}%) {lob_lines[lob]:,} lines")

# Delivery mode
deliv_rev = defaultdict(float)
deliv_lines = defaultdict(int)
for r in all_sales:
    deliv_rev[r['delivery']] += r['jumlah']
    deliv_lines[r['delivery']] += 1

print(f"\nDELIVERY MODE:")
for d in sorted(deliv_rev.keys(), key=lambda x: deliv_rev[x], reverse=True):
    pct = deliv_rev[d]/total_revenue*100
    print(f"  {d or '(kosong)'}: Rp {deliv_rev[d]/1e9:>10.1f}M ({pct:>5.1f}%) {deliv_lines[d]:,} lines")

# Avg transaction
print(f"\nAVERAGES:")
print(f"  Per line item: Rp {total_revenue/total_lines:,.0f}")
print(f"  Per invoice: Rp {total_revenue/unique_invoices:,.0f}")

# Supplier mapping
mapped = sum(1 for r in all_sales if r['supplier'])
unmapped_grups = set(r['grup_item'] for r in all_sales if not r['supplier'])
print(f"\nSUPPLIER MAPPING:")
print(f"  Mapped: {mapped:,} / {total_lines:,} ({mapped/total_lines*100:.1f}%)")
print(f"  Unmapped groups: {sorted(unmapped_grups)}")

# Discount analysis
disc_lines = sum(1 for r in all_sales if r['diskon'] > 0)
disc_total = sum(r['diskon'] for r in all_sales)
print(f"\nDISCOUNT ANALYSIS:")
print(f"  Lines with discount: {disc_lines:,} / {total_lines:,} ({disc_lines/total_lines*100:.1f}%)")
print(f"  Total discount value: Rp {disc_total:,.0f}")
print(f"  Avg discount (when applied): Rp {disc_total/disc_lines:,.0f}" if disc_lines else "")

print(f"\nDONE.")
