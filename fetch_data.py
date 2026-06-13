#!/usr/bin/env python3
"""Fetch & process all SNA data sources into dashboard JSON with filter support."""
import csv, json, os
from collections import defaultdict

def parse_num(s):
    """US format: commas = thousands, dot = decimal."""
    if not s or not s.strip(): return 0
    s = s.strip().replace(' ','').replace('"','').replace(',','')
    try: return float(s)
    except: return 0

def parse_num_id(s):
    """Indonesian format: dots = thousands, comma = decimal."""
    if not s or not s.strip(): return 0
    s = s.strip().replace(' ','').replace('"','').replace('.','').replace(',','.')
    try: return float(s)
    except: return 0

def load_csv(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return list(csv.reader(f))

# ============================================================
# MASTER DATA
# ============================================================
print("Loading master data...")
items_raw = load_csv('/root/master_list_items.csv')
item_map = {}
group_name_map = {}
class_name_map = {}
item_class_map = {}  # item_code → class_code
for row in items_raw[1:]:
    if len(row) >= 5:
        item_map[row[0].strip()] = {'nama':row[1].strip(),'group':row[3].strip()}
    if len(row) >= 6 and row[4].strip() and row[5].strip():
        group_name_map[row[4].strip()] = row[5].strip()
    if len(row) >= 8 and row[6].strip() and row[7].strip():
        class_name_map[row[6].strip()] = row[7].strip()
    if len(row) >= 7 and row[1].strip() and row[6].strip():
        item_class_map[row[1].strip()] = row[6].strip()

# ============================================================
# SALES DATA
# ============================================================
print("Loading sales data...")
month_map = {'Jan':'Jan','Feb':'Feb','Mar':'Mar','Apr':'Apr','Mei':'May','May':'May',
             'Jun':'Jun','Jul':'Jul','Agt':'Aug','Aug':'Aug','Sep':'Sep',
             'Okt':'Oct','Oct':'Oct','Nov':'Nov','Des':'Dec','Dec':'Dec'}
month_order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

sales = []
for fname, year in [('/tmp/sheet_a.csv', 2025), ('/tmp/sheet_b.csv', 2026)]:
    rows = load_csv(fname)
    for row in rows[2:]:
        if len(row) < 12: continue
        tanggal = row[2].strip() if len(row) > 2 else ''
        bulan = ''
        if tanggal:
            parts = tanggal.split('-')
            if len(parts) >= 2:
                bulan = month_map.get(parts[1], parts[1])
        if not bulan and len(row) > 41:
            bulan = month_map.get(row[41].strip(), '')
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
            'jumlah': parse_num(row[11]),
            'sales': row[14].strip() if len(row) > 14 else '',
            'lob': row[17].strip() if len(row) > 17 else '',
            'delivery': row[19].strip() if len(row) > 19 else '',
        })

print(f"  Sales rows: {len(sales)}")

# Unique filter values
all_branches = sorted(set(s['cabang'] for s in sales if s['cabang']))
all_months = month_order
all_items = sorted(set(s['item'] for s in sales))

# ============================================================
# STOCK DATA
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

# ============================================================
# PROCUREMENT DATA
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

all_suppliers = sorted(set(p['supplier'] for p in proc if p['supplier'] and p['status']!='Batal'))

# ============================================================
# STOCK VS SALES VELOCITY (computed fresh each time based on filters)
# ============================================================
print("Computing stock vs sales velocity...")
item_monthly_qty = defaultdict(float)
for s in sales:
    if s['tahun'] == 2026:
        item_monthly_qty[s['item']] += s['qty']

stock_by_item = defaultdict(lambda: {'akhir':0, 'in':0, 'out':0, 'nama':''})
for s in stock:
    si = stock_by_item[s['item_code']]
    si['akhir'] += s['akhir']; si['in'] += s['in']; si['out'] += s['out']; si['nama'] = s['nama']

stock_vs_sales_all = []
for item_code, si in stock_by_item.items():
    velocity = item_monthly_qty.get(item_code, 0) / 4
    stock_qty = si['akhir']
    mos = stock_qty / velocity if velocity > 0 else 999
    status = 'OK'
    if velocity == 0 and stock_qty > 0: status = 'NO_MOVEMENT'
    elif mos > 6: status = 'OVERSTOCK'
    elif mos < 1: status = 'LOW_STOCK'
    elif mos < 2: status = 'WATCH'
    stock_vs_sales_all.append({
        'item': item_code, 'nama': si['nama'],
        'stock': stock_qty, 'velocity': round(velocity, 1),
        'mos': round(min(mos, 999), 1), 'status': status,
    })

# ============================================================
# GENERATE FILTERABLE DASHBOARD JSON
# ============================================================
print("Generating dashboard JSON...")

# Helper: aggregate sales with optional filters
def agg_sales(branch=None, months=None, supplier=None):
    """Aggregate sales data with optional filters. Returns dict with all aggregations."""
    filtered = sales
    if branch:
        filtered = [s for s in filtered if s['cabang'] == branch]
    if months:
        filtered = [s for s in filtered if s['bulan'] in months]
    # Supplier filter: map supplier → item codes via procurement
    if supplier:
        sup_items = set(p['kode'] for p in proc if p['supplier'] == supplier)
        filtered = [s for s in filtered if s['item'] in sup_items]

    total_25 = sum(s['jumlah'] for s in filtered if s['tahun']==2025)
    total_26 = sum(s['jumlah'] for s in filtered if s['tahun']==2026)

    # Monthly
    monthly = {'2025': defaultdict(float), '2026': defaultdict(float)}
    for s in filtered:
        monthly[str(s['tahun'])][s['bulan']] += s['jumlah']

    # Branch
    br = defaultdict(lambda: {'rev25':0,'rev26':0})
    br_monthly = defaultdict(lambda: defaultdict(lambda: {'rev25':0,'rev26':0}))
    for s in filtered:
        if s['tahun']==2025: br[s['cabang']]['rev25'] += s['jumlah']
        else: br[s['cabang']]['rev26'] += s['jumlah']
        if s['tahun']==2025: br_monthly[s['cabang']][s['bulan']]['rev25'] += s['jumlah']
        else: br_monthly[s['cabang']][s['bulan']]['rev26'] += s['jumlah']
    br_sorted = sorted(br.items(), key=lambda x: x[1]['rev25'], reverse=True)

    # Product groups
    gr = defaultdict(float)
    # Per-group class breakdown
    gr_class = defaultdict(lambda: defaultdict(float))
    # Year-specific product groups
    gr_25 = defaultdict(float)
    gr_26 = defaultdict(float)
    gr_class_25 = defaultdict(lambda: defaultdict(float))
    gr_class_26 = defaultdict(lambda: defaultdict(float))
    for s in filtered:
        gr[s['grup_item']] += s['jumlah']
        cls = item_class_map.get(s['item'], '')
        if cls:
            gr_class[s['grup_item']][cls] += s['jumlah']
        if s['tahun']==2025:
            gr_25[s['grup_item']] += s['jumlah']
            if cls: gr_class_25[s['grup_item']][cls] += s['jumlah']
        else:
            gr_26[s['grup_item']] += s['jumlah']
            if cls: gr_class_26[s['grup_item']][cls] += s['jumlah']
    gr_sorted = sorted(gr.items(), key=lambda x: x[1], reverse=True)[:12]

    # Items
    it_rev = defaultdict(float)
    it_qty = defaultdict(float)
    it_name = {}
    it_year = defaultdict(set)  # item → set of years
    for s in filtered:
        it_rev[s['item']] += s['jumlah']
        it_qty[s['item']] += s['qty']
        it_year[s['item']].add(s['tahun'])
        if s['keterangan']: it_name[s['item']] = s['keterangan']
    top_items = sorted(it_rev.items(), key=lambda x: x[1], reverse=True)[:15]
    total_sku_25 = sum(1 for yrs in it_year.values() if 2025 in yrs)
    total_sku_26 = sum(1 for yrs in it_year.values() if 2026 in yrs)

    # Customers
    cu = defaultdict(float)
    cu_name = {}
    for s in filtered:
        if s['kode_pelanggan']:
            cu[s['kode_pelanggan']] += s['jumlah']
            cu_name[s['kode_pelanggan']] = s['pelanggan']
    top_custs = sorted(cu.items(), key=lambda x: x[1], reverse=True)[:20]

    # LOB
    lo = defaultdict(float)
    for s in filtered:
        lo[s['lob']] += s['jumlah']
    lo_sorted = sorted(lo.items(), key=lambda x: x[1], reverse=True)

    # Sales by person (per salesperson code)
    sp = defaultdict(lambda: {'revenue':0,'qty':0,'customers':set(),'cust25':set(),'cust26':set(),'rev25':0,'rev26':0,'qty25':0,'qty26':0})
    for s in filtered:
        if s['sales']:
            sp[s['sales']]['revenue'] += s['jumlah']
            sp[s['sales']]['qty'] += s['qty']
            if s['kode_pelanggan']: sp[s['sales']]['customers'].add(s['kode_pelanggan'])
            if s['tahun']==2025:
                sp[s['sales']]['rev25'] += s['jumlah']
                sp[s['sales']]['qty25'] += s['qty']
                if s['kode_pelanggan']: sp[s['sales']]['cust25'].add(s['kode_pelanggan'])
            else:
                sp[s['sales']]['rev26'] += s['jumlah']
                sp[s['sales']]['qty26'] += s['qty']
                if s['kode_pelanggan']: sp[s['sales']]['cust26'].add(s['kode_pelanggan'])
    sp_list = [{'code':k,'revenue':v['revenue'],'qty':v['qty'],'customers':len(v['customers']),'cust25':len(v['cust25']),'cust26':len(v['cust26']),'rev25':v['rev25'],'rev26':v['rev26'],'qty25':v['qty25'],'qty26':v['qty26']} for k,v in sp.items()]
    sp_list.sort(key=lambda x: x['revenue'], reverse=True)

    return {
        'total25': total_25, 'total26': total_26,
        'monthly': {'labels': month_order, 'y2025': [monthly['2025'].get(m,0) for m in month_order], 'y2026': [monthly['2026'].get(m,0) for m in month_order]},
        'branches': {'labels':[b[0] for b in br_sorted],'rev25':[b[1]['rev25'] for b in br_sorted],'rev26':[b[1]['rev26'] for b in br_sorted]},
        'branch_monthly': {br_name: {m: {'rev25': br_monthly[br_name][m]['rev25'], 'rev26': br_monthly[br_name][m]['rev26']} for m in month_order} for br_name in br_monthly},
        'products': {'labels':[g[0] for g in gr_sorted],'values':[g[1] for g in gr_sorted],'classes':{g[0]:dict(sorted(gr_class.get(g[0],{}).items(), key=lambda x:x[1], reverse=True)) for g in gr_sorted},
            'values25':[gr_25.get(g[0],0) for g in gr_sorted],'values26':[gr_26.get(g[0],0) for g in gr_sorted],
            'classes25':{g[0]:dict(sorted(gr_class_25.get(g[0],{}).items(), key=lambda x:x[1], reverse=True)) for g in gr_sorted},
            'classes26':{g[0]:dict(sorted(gr_class_26.get(g[0],{}).items(), key=lambda x:x[1], reverse=True)) for g in gr_sorted}},
        'items': [{'kode':i[0],'nama':it_name.get(i[0],i[0])[:40],'revenue':i[1],'qty':it_qty[i[0]]} for i in top_items],
        'total_sku': len(it_rev),
        'total_sku_25': total_sku_25,
        'total_sku_26': total_sku_26,
        'customers': [{'kode':c[0],'nama':cu_name.get(c[0],'')[:30],'revenue':c[1]} for c in top_custs],
        'lob': {'labels':[l[0] for l in lo_sorted],'values':[l[1] for l in lo_sorted]},
        'salespersons': sp_list[:20],
    }

# Pre-compute default (all data)
default_sales = agg_sales()

# Pre-compute per-branch aggregations (for fast filter response)
branch_sales_cache = {}
for br in all_branches:
    branch_sales_cache[br] = agg_sales(branch=br)

# Pre-compute per-month aggregations
month_sales_cache = {}
for m in all_months:
    month_sales_cache[m] = agg_sales(months=[m])

# Pre-compute per-branch-per-month caches (for accurate SKU counts)
branch_month_cache = {}
for br in all_branches:
    branch_month_cache[br] = {}
    for m in all_months:
        branch_month_cache[br][m] = agg_sales(branch=br, months=[m])

# Supplier → item codes mapping
supplier_items = defaultdict(set)
for p in proc:
    if p['status'] != 'Batal' and p['supplier'] and p['kode']:
        supplier_items[p['supplier']].add(p['kode'])

# Pre-compute per-supplier caches (for sales tab supplier filter)
supplier_sales_cache = {}
# Per-supplier per-branch salesperson cache
supplier_branch_sp = {}
for sup in all_suppliers:
    sup_codes = supplier_items.get(sup, set())
    if sup_codes:
        supplier_sales_cache[sup] = agg_sales(supplier=sup)
        # Build per-branch salesperson data for this supplier
        sup_sales = [s for s in sales if s['item'] in sup_codes]
        br_sp = defaultdict(lambda: defaultdict(lambda: {'revenue':0,'qty':0,'customers':set(),'cust25':set(),'cust26':set(),'rev25':0,'rev26':0,'qty25':0,'qty26':0}))
        br_month_sp = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'revenue':0,'qty':0,'customers':set(),'cust25':set(),'cust26':set(),'rev25':0,'rev26':0,'qty25':0,'qty26':0})))
        for s in sup_sales:
            if s['sales']:
                br, m, sp = s['cabang'], s['bulan'], s['sales']
                br_sp[br][sp]['revenue'] += s['jumlah']
                br_sp[br][sp]['qty'] += s['qty']
                if s['kode_pelanggan']: br_sp[br][sp]['customers'].add(s['kode_pelanggan'])
                br_month_sp[br][m][sp]['revenue'] += s['jumlah']
                br_month_sp[br][m][sp]['qty'] += s['qty']
                if s['kode_pelanggan']: br_month_sp[br][m][sp]['customers'].add(s['kode_pelanggan'])
                if s['tahun']==2025:
                    br_sp[br][sp]['rev25'] += s['jumlah']; br_sp[br][sp]['qty25'] += s['qty']
                    if s['kode_pelanggan']: br_sp[br][sp]['cust25'].add(s['kode_pelanggan'])
                    br_month_sp[br][m][sp]['rev25'] += s['jumlah']; br_month_sp[br][m][sp]['qty25'] += s['qty']
                    if s['kode_pelanggan']: br_month_sp[br][m][sp]['cust25'].add(s['kode_pelanggan'])
                else:
                    br_sp[br][sp]['rev26'] += s['jumlah']; br_sp[br][sp]['qty26'] += s['qty']
                    if s['kode_pelanggan']: br_sp[br][sp]['cust26'].add(s['kode_pelanggan'])
                    br_month_sp[br][m][sp]['rev26'] += s['jumlah']; br_month_sp[br][m][sp]['qty26'] += s['qty']
                    if s['kode_pelanggan']: br_month_sp[br][m][sp]['cust26'].add(s['kode_pelanggan'])
        # Convert sets to counts
        sup_br = {}
        for br_name, sp_dict in br_sp.items():
            sp_list = [{'code':k,'revenue':v['revenue'],'qty':v['qty'],'customers':len(v['customers']),'cust25':len(v['cust25']),'cust26':len(v['cust26']),'rev25':v['rev25'],'rev26':v['rev26'],'qty25':v['qty25'],'qty26':v['qty26']} for k,v in sp_dict.items()]
            sp_list.sort(key=lambda x: x['revenue'], reverse=True)
            sup_br[br_name] = sp_list
        supplier_branch_sp[sup] = sup_br
        # Also store branch-month salesperson data
        sup_br_month = {}
        for br_name, months_dict in br_month_sp.items():
            sup_br_month[br_name] = {}
            for m_name, sp_dict in months_dict.items():
                sp_list = [{'code':k,'revenue':v['revenue'],'qty':v['qty'],'customers':len(v['customers']),'cust25':len(v['cust25']),'cust26':len(v['cust26']),'rev25':v['rev25'],'rev26':v['rev26'],'qty25':v['qty25'],'qty26':v['qty26']} for k,v in sp_dict.items()]
                sp_list.sort(key=lambda x: x['revenue'], reverse=True)
                sup_br_month[br_name][m_name] = {'salespersons': sp_list}
        supplier_branch_sp[sup + '_months'] = sup_br_month

# ============================================================
# PROCUREMENT aggregation with filters
# ============================================================
def agg_procurement(supplier=None, region=None):
    filtered = [p for p in proc if p['status']!='Batal']
    if supplier:
        filtered = [p for p in filtered if p['supplier'] == supplier]
    if region:
        filtered = [p for p in filtered if p['reg'] == region]

    status_count = defaultdict(int)
    by_reg = defaultdict(lambda: {'count':0,'nilai':0,'berat':0})
    by_sup = defaultdict(lambda: {'count':0,'nilai':0})
    by_kat = defaultdict(lambda: {'count':0,'nilai':0})
    for p in filtered:
        status_count[p['status']] += 1
        r = by_reg[p['reg']]; r['count']+=1; r['nilai']+=p['nilai_beli']; r['berat']+=p['total_berat']
        by_sup[p['supplier']]['count']+=1; by_sup[p['supplier']]['nilai']+=p['nilai_beli']
        by_kat[p['kategori']]['count']+=1; by_kat[p['kategori']]['nilai']+=p['nilai_beli']

    sup_sorted = sorted(by_sup.items(), key=lambda x: x[1]['nilai'], reverse=True)[:10]
    kat_sorted = sorted(by_kat.items(), key=lambda x: x[1]['nilai'], reverse=True)[:10]
    reg_sorted = sorted(by_reg.items(), key=lambda x: x[1]['nilai'], reverse=True)

    return {
        'total': len(filtered),
        'nilai': sum(p['nilai_beli'] for p in filtered),
        'pipeline': {'labels':['Estimasi Supply','Disetujui Manager','Perjalanan','Sudah Diterima'],'values':[status_count.get(s,0) for s in ['Estimasi Supply','Disetujui Manager','Perjalanan','Sudah Diterima']]},
        'regions': {'labels':[r[0] for r in reg_sorted],'count':[r[1]['count'] for r in reg_sorted],'nilai':[r[1]['nilai'] for r in reg_sorted],'berat':[r[1]['berat'] for r in reg_sorted]},
        'suppliers': {'labels':[s[0][:25] for s in sup_sorted],'count':[s[1]['count'] for s in sup_sorted],'nilai':[s[1]['nilai'] for s in sup_sorted]},
        'categories': {'labels':[k[0] for k in kat_sorted],'count':[k[1]['count'] for k in kat_sorted],'nilai':[k[1]['nilai'] for k in kat_sorted]},
    }

default_proc = agg_procurement()

# ============================================================
# STOCK aggregation with filters
# ============================================================
def agg_stock(branch=None):
    filtered = stock
    if branch:
        filtered = [s for s in stock if s['cabang'] == branch]

    by_branch = defaultdict(lambda: {'items':0,'akhir':0,'in':0,'out':0})
    by_item = defaultdict(lambda: {'akhir':0,'in':0,'out':0,'nama':''})
    for s in filtered:
        b = by_branch[s['cabang']]; b['items']+=1; b['akhir']+=s['akhir']; b['in']+=s['in']; b['out']+=s['out']
        si = by_item[s['item_code']]; si['akhir']+=s['akhir']; si['in']+=s['in']; si['out']+=s['out']; si['nama']=s['nama']

    br_sorted = sorted(by_branch.items(), key=lambda x: x[1]['akhir'], reverse=True)
    top_items = sorted(by_item.items(), key=lambda x: x[1]['akhir'], reverse=True)[:20]

    return {
        'branches': {'labels':[b[0] for b in br_sorted],'items':[b[1]['items'] for b in br_sorted],'akhir':[b[1]['akhir'] for b in br_sorted],'masuk':[b[1]['in'] for b in br_sorted],'keluar':[b[1]['out'] for b in br_sorted]},
        'items': [{'item':s[0],'nama':s[1]['nama'][:40],'akhir':s[1]['akhir'],'masuk':s[1]['in'],'keluar':s[1]['out']} for s in top_items],
    }

default_stock = agg_stock()

# ============================================================
# COMPILE FINAL JSON
# ============================================================
# KPIs
kpis = {
    'rev2025': default_sales['total25'],
    'rev2026': default_sales['total26'],
    'rev2026_ann': default_sales['total26'] / 4 * 12,
    'growth': round((default_sales['total26']/4*12 / default_sales['total25'] - 1) * 100, 1) if default_sales['total25'] else 0,
    'customers': len(set(s['kode_pelanggan'] for s in sales if s['kode_pelanggan'])),
    'skus': len(set(s['item'] for s in sales)),
    'branches': len(set(s['cabang'] for s in sales)),
    'stock_items': len(stock),
    'stock_unique': len(stock_by_item),
    'po_total': len([p for p in proc if p['status']!='Batal']),
    'po_nilai': sum(p['nilai_beli'] for p in proc if p['status']!='Batal'),
    'po_suppliers': len(set(p['supplier'] for p in proc if p['status']!='Batal')),
}

# SV summary
sv_summary = defaultdict(int)
for s in stock_vs_sales_all:
    sv_summary[s['status']] += 1

# Stock vs sales items (problems only, sorted by priority)
priority = {'LOW_STOCK':0, 'WATCH':1, 'OVERSTOCK':2, 'NO_MOVEMENT':3, 'OK':4}
sv_items = sorted([s for s in stock_vs_sales_all if s['status']!='OK'], key=lambda x: (priority.get(x['status'],5), -x.get('sales_rev',0)))[:50]
# Add sales_rev to sv_items
item_rev_map = defaultdict(float)
for s in sales:
    item_rev_map[s['item']] += s['jumlah']
for sv in sv_items:
    sv['sales_rev'] = item_rev_map.get(sv['item'], 0)

supplier_items_map = {k: list(v) for k, v in supplier_items.items()}

dashboard = {
    'filters': {
        'branches': all_branches,
        'months': all_months,
        'suppliers': all_suppliers,
        'supplier_items': supplier_items_map,
        'group_names': group_name_map,
        'class_names': class_name_map,
    },
    'kpis': kpis,
    'default': {
        'sales': default_sales,
        'stock': default_stock,
        'procurement': default_proc,
        'stock_vs_sales': {'summary': dict(sv_summary), 'items': sv_items},
    },
    # Pre-computed per-branch caches for fast filtering
    'branch_cache': branch_sales_cache,
    'month_cache': month_sales_cache,
    'branch_month_cache': branch_month_cache,
    'supplier_cache': supplier_sales_cache,
    'supplier_branch_sp': supplier_branch_sp,
}

out_path = '/root/sna-dashboard/dashboard_data.json'
with open(out_path, 'w') as f:
    json.dump(dashboard, f)

size = os.path.getsize(out_path)
print(f"\n✅ Dashboard JSON: {size:,} bytes ({size/1024:.0f} KB)")
print(f"Filters: {len(all_branches)} branches, {len(all_months)} months, {len(all_suppliers)} suppliers")
print(f"Sales: {len(sales)} rows")
print(f"Branch cache: {len(branch_sales_cache)} entries")
print(f"Month cache: {len(month_sales_cache)} entries")
