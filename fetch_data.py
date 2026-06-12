#!/usr/bin/env python3
"""Fetch & process all SNA data sources into dashboard JSON."""
import csv, json, os
from collections import defaultdict

def parse_num(s):
    """US format: commas = thousands, dot = decimal. For sales/stock data."""
    if not s or not s.strip(): return 0
    s = s.strip().replace(' ','').replace('"','').replace(',','')
    try: return float(s)
    except: return 0

def parse_num_id(s):
    """Indonesian format: dots = thousands, comma = decimal. For procurement data."""
    if not s or not s.strip(): return 0
    s = s.strip().replace(' ','').replace('"','').replace('.','').replace(',','.')
    try: return float(s)
    except: return 0

def load_csv(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return list(csv.reader(f))

# ============================================================
# 1. MASTER DATA
# ============================================================
print("Loading master data...")
items_raw = load_csv('/root/master_list_items.csv')
item_map = {}
for row in items_raw[1:]:
    if len(row) >= 5:
        item_map[row[0].strip()] = {'nama':row[1].strip(),'group':row[3].strip()}

suppliers_raw = load_csv('/root/master_supplier_list.csv')
supplier_map = {}
for row in suppliers_raw[1:]:
    if len(row) >= 2:
        supplier_map[row[1].strip()] = row[0].strip()

print(f"  Items: {len(item_map)}, Suppliers: {len(supplier_map)}")

# ============================================================
# 2. SALES DATA (header in row 1, data from row 2)
# ============================================================
print("Loading sales data...")
month_name_to_code = {'Jan':'Jan','Feb':'Feb','Mar':'Mar','Apr':'Apr','Mei':'May','May':'May',
                       'Jun':'Jun','Jul':'Jul','Agt':'Aug','Aug':'Aug','Sep':'Sep',
                       'Okt':'Oct','Oct':'Oct','Nov':'Nov','Des':'Dec','Dec':'Dec'}

sales = []
for fname, year in [('/tmp/sheet_a.csv', 2025), ('/tmp/sheet_b.csv', 2026)]:
    rows = load_csv(fname)
    header = [h.strip() for h in rows[1]]
    # Build index map
    idx = {h: i for i, h in enumerate(header)}
    for row in rows[2:]:
        if len(row) < 12: continue
        # Parse bulan from Tanggal col [2]: "1-Jan-25"
        tanggal = row[2].strip() if len(row) > 2 else ''
        bulan = ''
        if tanggal:
            parts = tanggal.split('-')
            if len(parts) >= 2:
                bulan = month_name_to_code.get(parts[1], parts[1])
        # Fallback: col 41 (Bulan) for 2025
        if not bulan and len(row) > 41:
            bulan = month_name_to_code.get(row[41].strip(), '')
        if not bulan: continue

        sales.append({
            'tahun': year,
            'bulan': bulan,
            'cabang': row[1].strip(),
            'kode_pelanggan': row[3].strip(),
            'pelanggan': row[4].strip(),
            'grup_item': row[6].strip(),
            'item': row[7].strip(),
            'keterangan': row[20].strip() if len(row) > 20 else '',
            'qty': parse_num(row[8]),
            'harga': parse_num(row[9]),
            'diskon': parse_num(row[10]),
            'jumlah': parse_num(row[11]),
            'lob': row[17].strip() if len(row) > 17 else '',
            'delivery': row[19].strip() if len(row) > 19 else '',
        })

print(f"  Sales rows: {len(sales)}")

# Sales aggregation
month_order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
monthly_rev = {'2025': defaultdict(float), '2026': defaultdict(float)}
branch_rev = defaultdict(lambda: {'rev25':0,'rev26':0,'qty25':0,'qty26':0})
item_rev = defaultdict(float)
item_qty = defaultdict(float)
item_name = {}
grup_rev = defaultdict(float)
cust_rev = defaultdict(float)
cust_name = {}
lob_rev = defaultdict(float)
deliv_rev = defaultdict(float)

for s in sales:
    yr = str(s['tahun'])
    monthly_rev[yr][s['bulan']] += s['jumlah']
    key = s['cabang']
    if s['tahun'] == 2025:
        branch_rev[key]['rev25'] += s['jumlah']
        branch_rev[key]['qty25'] += s['qty']
    else:
        branch_rev[key]['rev26'] += s['jumlah']
        branch_rev[key]['qty26'] += s['qty']
    item_rev[s['item']] += s['jumlah']
    item_qty[s['item']] += s['qty']
    if s['keterangan']: item_name[s['item']] = s['keterangan']
    grup_rev[s['grup_item']] += s['jumlah']
    if s['kode_pelanggan']:
        cust_rev[s['kode_pelanggan']] += s['jumlah']
        cust_name[s['kode_pelanggan']] = s['pelanggan']
    lob_rev[s['lob']] += s['jumlah']
    deliv_rev[s['delivery']] += s['jumlah']

# ============================================================
# 3. STOCK DATA
# ============================================================
print("Loading stock data...")
stock_rows = load_csv('/tmp/stock_sheet.csv')
stock = []
for row in stock_rows[5:]:
    if len(row) < 8 or not row[0].strip(): continue
    stock.append({
        'cabang': row[0].strip(),
        'gudang': row[1].strip(),
        'item_code': row[2].strip(),
        'nama': row[3].strip(),
        'awal': parse_num(row[4]),
        'in': parse_num(row[5]),
        'out': parse_num(row[6]),
        'akhir': parse_num(row[7]),
    })
print(f"  Stock rows: {len(stock)}")

stock_by_branch = defaultdict(lambda: {'items':0, 'akhir':0, 'in':0, 'out':0})
stock_by_item = defaultdict(lambda: {'akhir':0, 'in':0, 'out':0, 'nama':''})
for s in stock:
    b = stock_by_branch[s['cabang']]
    b['items'] += 1; b['akhir'] += s['akhir']; b['in'] += s['in']; b['out'] += s['out']
    si = stock_by_item[s['item_code']]
    si['akhir'] += s['akhir']; si['in'] += s['in']; si['out'] += s['out']; si['nama'] = s['nama']

# ============================================================
# 4. PROCUREMENT DATA
# ============================================================
print("Loading procurement data...")
proc_rows = load_csv('/tmp/djabes_sheet.csv')
proc = []
for row in proc_rows[2:]:
    if len(row) < 10 or not row[1].strip(): continue
    proc.append({
        'status': row[1].strip(),
        'reg': row[2].strip(),
        'cab': row[3].strip(),
        'po': row[5].strip(),
        'kode': row[6].strip(),
        'nama': row[7].strip(),
        'kategori': row[8].strip(),
        'supplier': row[9].strip(),
        'qty_po': parse_num_id(row[11]),
        'nilai_beli': parse_num_id(row[14]),
        'tgl_po': row[16].strip() if len(row) > 16 else '',
        'total_berat': parse_num_id(row[19]) if len(row) > 19 else 0,
    })
print(f"  Procurement rows: {len(proc)}")

proc_status = defaultdict(int)
proc_by_reg = defaultdict(lambda: {'count':0, 'nilai':0, 'berat':0})
proc_by_supplier = defaultdict(lambda: {'count':0, 'nilai':0})
proc_by_kategori = defaultdict(lambda: {'count':0, 'nilai':0})

for p in proc:
    if p['status'] == 'Batal': continue
    proc_status[p['status']] += 1
    r = proc_by_reg[p['reg']]
    r['count'] += 1; r['nilai'] += p['nilai_beli']; r['berat'] += p['total_berat']
    proc_by_supplier[p['supplier']]['count'] += 1
    proc_by_supplier[p['supplier']]['nilai'] += p['nilai_beli']
    proc_by_kategori[p['kategori']]['count'] += 1
    proc_by_kategori[p['kategori']]['nilai'] += p['nilai_beli']

# ============================================================
# 5. STOCK VS SALES VELOCITY
# ============================================================
print("Computing stock vs sales velocity...")
item_monthly_qty = defaultdict(float)
for s in sales:
    if s['tahun'] == 2026:
        item_monthly_qty[s['item']] += s['qty']

stock_vs_sales = []
for item_code, stock_info in stock_by_item.items():
    velocity = item_monthly_qty.get(item_code, 0) / 4  # avg per month
    stock_qty = stock_info['akhir']
    months_of_stock = stock_qty / velocity if velocity > 0 else 999
    status = 'OK'
    if velocity == 0 and stock_qty > 0: status = 'NO_MOVEMENT'
    elif months_of_stock > 6: status = 'OVERSTOCK'
    elif months_of_stock < 1: status = 'LOW_STOCK'
    elif months_of_stock < 2: status = 'WATCH'
    stock_vs_sales.append({
        'item': item_code, 'nama': stock_info['nama'],
        'stock': stock_qty, 'velocity': round(velocity, 1),
        'mos': round(min(months_of_stock, 999), 1), 'status': status,
        'sales_rev': item_rev.get(item_code, 0),
    })

sv_status = defaultdict(int)
for s in stock_vs_sales:
    sv_status[s['status']] += 1

# Sort: problems first
priority = {'LOW_STOCK':0, 'WATCH':1, 'OVERSTOCK':2, 'NO_MOVEMENT':3, 'OK':4}
stock_vs_sales.sort(key=lambda x: (priority.get(x['status'],5), -x['sales_rev']))

# ============================================================
# 6. GENERATE DASHBOARD JSON
# ============================================================
print("Generating dashboard JSON...")
total_rev_25 = sum(s['jumlah'] for s in sales if s['tahun']==2025)
total_rev_26 = sum(s['jumlah'] for s in sales if s['tahun']==2026)
kpis = {
    'rev2025': total_rev_25,
    'rev2026': total_rev_26,
    'rev2026_ann': total_rev_26 / 4 * 12,
    'growth': round((total_rev_26/4*12 / total_rev_25 - 1) * 100, 1) if total_rev_25 else 0,
    'customers': len(set(s['kode_pelanggan'] for s in sales if s['kode_pelanggan'])),
    'skus': len(set(s['item'] for s in sales)),
    'branches': len(set(s['cabang'] for s in sales)),
    'stock_items': len(stock),
    'stock_unique': len(stock_by_item),
    'po_total': len([p for p in proc if p['status']!='Batal']),
    'po_nilai': sum(p['nilai_beli'] for p in proc if p['status']!='Batal'),
    'po_suppliers': len(set(p['supplier'] for p in proc if p['status']!='Batal')),
}

grup_nama_map = {
    '01TRP':'Triplek','02GRC':'GRC Board','03PKU':'Paku','04KB':'Kawat',
    '05SGG':'Seng','05TLG':'Talang','06HL':'Hollow','08TRMK':'Triplek MRK',
    '08SPDK':'Spandek','10PMP':'Pipa PVC','10PGLW':'Pipa Galv',
    '15BJR':'Baja Ringan','16BL':'Bata Ringan','19LMF':'Lem Fox',
    '20DJ':'Djabesmen','28GPSM':'Gypsum','30KBL':'Kabel','35ASPL':'Aspal',
}

grup_sorted = sorted(grup_rev.items(), key=lambda x: x[1], reverse=True)[:12]
branch_sorted = sorted(branch_rev.items(), key=lambda x: x[1]['rev25'], reverse=True)
top_items_list = sorted(item_rev.items(), key=lambda x: x[1], reverse=True)[:15]
sorted_custs = sorted(cust_rev.items(), key=lambda x: x[1], reverse=True)

# Pareto
total_cust_rev = sum(cust_rev.values())
cum = 0
pareto_points = []
for i, (k, v) in enumerate(sorted_custs):
    cum += v
    if i < 20 or i % 50 == 0 or i == len(sorted_custs)-1:
        pareto_points.append({'pctCust':round((i+1)/len(sorted_custs)*100,1),'pctRev':round(cum/total_cust_rev*100,1)})

lob_sorted_list = sorted(lob_rev.items(), key=lambda x: x[1], reverse=True)

# Stock
stock_branch_sorted = sorted(stock_by_branch.items(), key=lambda x: x[1]['akhir'], reverse=True)
top_stock = sorted(stock_by_item.items(), key=lambda x: x[1]['akhir'], reverse=True)[:20]

# Procurement
proc_reg_sorted = sorted(proc_by_reg.items(), key=lambda x: x[1]['nilai'], reverse=True)
proc_sup_sorted = sorted(proc_by_supplier.items(), key=lambda x: x[1]['nilai'], reverse=True)[:10]
proc_kat_sorted = sorted(proc_by_kategori.items(), key=lambda x: x[1]['nilai'], reverse=True)[:10]

dashboard = {
    'kpis': kpis,
    'monthly': {'labels': month_order, 'y2025': [monthly_rev['2025'].get(m,0) for m in month_order], 'y2026': [monthly_rev['2026'].get(m,0) for m in month_order]},
    'branches': {'labels':[b[0] for b in branch_sorted],'rev25':[b[1]['rev25'] for b in branch_sorted],'rev26':[b[1]['rev26'] for b in branch_sorted]},
    'products': {'labels':[grup_nama_map.get(g[0],g[0]) for g in grup_sorted],'values':[g[1] for g in grup_sorted]},
    'items': [{'kode':i[0],'nama':item_name.get(i[0],i[0])[:45],'revenue':i[1],'qty':item_qty[i[0]]} for i in top_items_list],
    'customers': [{'kode':c[0],'nama':cust_name.get(c[0],'')[:30],'revenue':c[1]} for c in sorted_custs[:20]],
    'pareto': pareto_points,
    'lob': {'labels':[l[0] for l in lob_sorted_list],'values':[l[1] for l in lob_sorted_list]},
    'stock': {
        'branches': {'labels':[b[0] for b in stock_branch_sorted],'items':[b[1]['items'] for b in stock_branch_sorted],'akhir':[b[1]['akhir'] for b in stock_branch_sorted],'masuk':[b[1]['in'] for b in stock_branch_sorted],'keluar':[b[1]['out'] for b in stock_branch_sorted]},
        'items': [{'item':s[0],'nama':s[1]['nama'][:40],'akhir':s[1]['akhir'],'masuk':s[1]['in'],'keluar':s[1]['out']} for s in top_stock],
        'vs_sales': {'summary': dict(sv_status), 'items': [s for s in stock_vs_sales if s['status']!='OK'][:50]},
    },
    'procurement': {
        'pipeline': {'labels':['Estimasi Supply','Disetujui Manager','Perjalanan','Sudah Diterima'],'values':[proc_status.get(s,0) for s in ['Estimasi Supply','Disetujui Manager','Perjalanan','Sudah Diterima']]},
        'regions': {'labels':[r[0] for r in proc_reg_sorted],'count':[r[1]['count'] for r in proc_reg_sorted],'nilai':[r[1]['nilai'] for r in proc_reg_sorted],'berat':[r[1]['berat'] for r in proc_reg_sorted]},
        'suppliers': {'labels':[s[0][:25] for s in proc_sup_sorted],'count':[s[1]['count'] for s in proc_sup_sorted],'nilai':[s[1]['nilai'] for s in proc_sup_sorted]},
        'categories': {'labels':[k[0] for k in proc_kat_sorted],'count':[k[1]['count'] for k in proc_kat_sorted],'nilai':[k[1]['nilai'] for k in proc_kat_sorted]},
    },
}

out_path = '/root/sna-dashboard/dashboard_data.json'
with open(out_path, 'w') as f:
    json.dump(dashboard, f)

print(f"\n✅ Dashboard JSON: {os.path.getsize(out_path):,} bytes")
print(f"Sales: {len(sales)} rows, Rev25=Rp{kpis['rev2025']/1e9:.1f}B, Rev26=Rp{kpis['rev2026']/1e9:.1f}B, Growth={kpis['growth']}%")
print(f"Stock: {kpis['stock_items']} items, {kpis['stock_unique']} unique SKUs")
print(f"PO: {kpis['po_total']} rows, Rp{kpis['po_nilai']/1e9:.1f}B")
print(f"Stock vs Sales: {dict(sv_status)}")
