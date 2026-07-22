#!/usr/bin/env python3
"""Generate dashboard JSON from PostgreSQL CSV exports (Jalur A).
Sumber: sales+stock+produk+customer dari PostgreSQL (via /tmp/pg_*.csv).
Master group/class names + procurement tetap dari file lokal.
Aggregation logic IDENTIK dengan fetch_data.py (Google Sheets)."""
import csv, json, os
from collections import defaultdict

def parse_num(s):
    if s is None: return 0
    s = str(s).strip().replace(' ','').replace('"','').replace(',','')
    try: return float(s)
    except: return 0

def parse_num_id(s):
    if s is None: return 0
    s = str(s).strip().replace(' ','').replace('"','').replace('.','').replace(',','.')
    try: return float(s)
    except: return 0

def load_csv(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return list(csv.reader(f))

month_map = {'Jan':'Jan','Feb':'Feb','Mar':'Mar','Apr':'Apr','Mei':'May','May':'May',
             'Jun':'Jun','Jul':'Jul','Agt':'Aug','Aug':'Aug','Sep':'Sep',
             'Okt':'Oct','Oct':'Oct','Nov':'Nov','Des':'Dec','Dec':'Dec'}
month_order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

PG_DIR = os.environ.get('PG_DIR', '/tmp')

# ============================================================
# MASTER DATA (dari PostgreSQL dim_master_item + dim_produk PG)
# ============================================================
print("Loading master data (PostgreSQL)...")
items_raw = load_csv(os.path.join(PG_DIR,'pg_master.csv'))
item_map = {}
group_name_map = {}
class_name_map = {}
class_name_votes = defaultdict(lambda: defaultdict(int))
item_class_map = {}
# pg_master: 0=kode 1=nama_barang 2=satuan 3=group_code 4=group_name 5=class_code 6=class_name 7=type_code 8=supplier
for row in items_raw[1:]:
    if len(row) >= 4:
        item_map[row[0].strip()] = {'nama':row[1].strip(),'group':row[3].strip()}
    if len(row) >= 5 and row[3].strip() and row[4].strip():
        group_name_map[row[3].strip()] = row[4].strip()
    if len(row) >= 7 and row[5].strip() and row[6].strip():
        class_name_votes[row[5].strip()][row[6].strip()] += 1
    if len(row) >= 6 and row[0].strip() and row[5].strip():
        item_class_map[row[0].strip()] = row[5].strip()
for code, votes in class_name_votes.items():
    class_name_map[code] = max(votes, key=votes.get)

# Merge dim_produk PG (untuk item yg tak ada di master CSV): grup_item, nama_item
produk_rows = load_csv(os.path.join(PG_DIR,'pg_produk.csv'))
# 0=kode_item 1=nama_item 2=grup_item 3=kategori_item 4=item_jp 5=satuan 6=kode_supplier 7=brand 8=supplier_name
produk_name = {}
for row in produk_rows[1:]:
    if len(row) < 3: continue
    code = row[0].strip()
    produk_name[code] = row[1].strip()
    if code not in item_map:
        item_map[code] = {'nama':row[1].strip(), 'group':row[2].strip()}

# Customer names dari PG
cust_rows = load_csv(os.path.join(PG_DIR,'pg_customer.csv'))
cust_name_map = {}
for row in cust_rows[1:]:
    if len(row) < 2: continue
    cust_name_map[row[0].strip()] = row[1].strip()

# ============================================================
# SALES DATA (dari PostgreSQL pg_sales.csv)
# ============================================================
print("Loading sales data (PostgreSQL)...")
sales_rows = load_csv(os.path.join(PG_DIR,'pg_sales.csv'))
# 0=nomor_invoice 1=tanggal 2=kode_cabang 3=kode_customer 4=kode_item 5=qty 6=harga
# 7=diskon 8=jumlah 9=total 10=status 11=sales 12=delivery 13=non_sales 14=bulan 15=lob
sales = []
for row in sales_rows[1:]:
    if len(row) < 15: continue
    tgl = row[1].strip()
    year = int(tgl[:4]) if len(tgl) >= 4 and tgl[:4].isdigit() else 0
    bulan = month_map.get(row[14].strip(), row[14].strip())
    if not bulan: continue
    item = row[4].strip()
    sales.append({
        'tahun': year,
        'bulan': bulan,
        'cabang': row[2].strip(),
        'kode_pelanggan': row[3].strip(),
        'pelanggan': cust_name_map.get(row[3].strip(), ''),
        'grup_item': item_map.get(item, {}).get('group', ''),
        'item': item,
        'keterangan': produk_name.get(item, item_map.get(item, {}).get('nama', '')),
        'qty': parse_num(row[5]),
        'harga': parse_num(row[6]),
        'jumlah': parse_num(row[8]),
        'sales': row[11].strip(),
        'lob': row[15].strip() if len(row) > 15 else '',
        'delivery': row[12].strip(),
    })
print(f"  Sales rows: {len(sales)}")

all_branches = sorted(set(s['cabang'] for s in sales if s['cabang']))
all_months = month_order
all_items = sorted(set(s['item'] for s in sales))

# ============================================================
# STOCK DATA (dari PostgreSQL pg_stock.csv)
# ============================================================
print("Loading stock data (PostgreSQL)...")
stock_rows = load_csv(os.path.join(PG_DIR,'pg_stock.csv'))
# 0=kode_cabang 1=kode_item 2=nama_item 3=qty_awal 4=qty_masuk 5=qty_keluar
# 6=qty_akhir 7=periode 8=wh 9=tanggal 10=nilai_stok 11=hrg_kirim 12=hrg_ambil
stock = []
for row in stock_rows[1:]:
    if len(row) < 11 or not row[0].strip(): continue
    stock.append({
        'cabang': row[0].strip(),
        'tanggal': row[7].strip(),   # pakai periode (Jan..Jul) supaya _parse_stock_month benar
        'gudang': row[8].strip(),
        'item_code': row[1].strip(),
        'nama': row[2].strip(),
        'awal': parse_num(row[3]),
        'in': parse_num(row[4]),
        'out': parse_num(row[5]),
        'akhir': parse_num(row[6]),
        'nilai': parse_num(row[10]),
    })
print(f"  Stock rows: {len(stock)}")

# ============================================================
# PROCUREMENT DATA (dari PostgreSQL fact_procurement)
# ============================================================
print("Loading procurement data (PostgreSQL)...")
proc = []
proc_path = os.path.join(PG_DIR,'pg_procurement.csv')
if os.path.exists(proc_path):
    proc_rows = load_csv(proc_path)
    # pg_procurement: 0=status 1=reg 2=cab 3=po 4=kode 5=nama 6=kategori 7=supplier 8=qty_po 9=nilai_beli 10=tgl_po 11=total_berat
    for row in proc_rows[1:]:
        if len(row) < 8 or not row[0].strip(): continue
        proc.append({
            'status': row[0].strip(), 'reg': row[1].strip(), 'cab': row[2].strip(),
            'po': row[3].strip(), 'kode': row[4].strip(), 'nama': row[5].strip(),
            'kategori': row[6].strip(), 'supplier': row[7].strip(),
            'qty_po': parse_num(row[8]), 'nilai_beli': parse_num(row[9]),
            'tgl_po': row[10].strip() if len(row) > 10 else '',
            'total_berat': parse_num(row[11]) if len(row) > 11 else 0,
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

# Stock nilai total & by group
stock_nilai_total = sum(s['nilai'] for s in stock)
stock_nilai_by_group = defaultdict(float)
for s in stock:
    code = s['item_code']
    grp = item_map.get(code, {}).get('group', '')
    if grp:
        grp_name = group_name_map.get(grp, grp)
        stock_nilai_by_group[grp_name] += s['nilai']
    else:
        stock_nilai_by_group['(Tanpa Group)'] += s['nilai']
stock_nilai_top_groups = sorted(stock_nilai_by_group.items(), key=lambda x: x[1], reverse=True)[:10]

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
def agg_sales(branch=None, months=None, supplier=None, group=None, class_month=False):
    """Aggregate sales data with optional filters. Returns dict with all aggregations.
    class_month=True adds products.classes_month[grp][month][cls]=[rev25,rev26] so the
    frontend can slice class breakdowns by selected months (used only for group_cache)."""
    filtered = sales
    if branch:
        filtered = [s for s in filtered if s['cabang'] == branch]
    if months:
        filtered = [s for s in filtered if s['bulan'] in months]
    # Supplier filter: map supplier → item codes via procurement
    if supplier:
        sup_items = set(p['kode'] for p in proc if p['supplier'] == supplier)
        filtered = [s for s in filtered if s['item'] in sup_items]
    # Group filter: only items belonging to the specified product group
    if group:
        filtered = [s for s in filtered if s['grup_item'] == group]

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
    # Per-group per-month class breakdown: gr_class_month[grp][month][cls] = [rev25, rev26]
    gr_class_month = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))) if class_month else None
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
        if class_month and cls:
            slot = gr_class_month[s['grup_item']][s['bulan']][cls]
            if s['tahun']==2025: slot[0] += s['jumlah']
            else: slot[1] += s['jumlah']
    gr_sorted = sorted(gr.items(), key=lambda x: x[1], reverse=True)[:12]

    # Items
    it_rev = defaultdict(float)
    it_qty = defaultdict(float)
    it_rev25 = defaultdict(float)
    it_rev26 = defaultdict(float)
    it_name = {}
    it_year = defaultdict(set)  # item → set of years
    for s in filtered:
        it_rev[s['item']] += s['jumlah']
        it_qty[s['item']] += s['qty']
        it_year[s['item']].add(s['tahun'])
        if s['keterangan']: it_name[s['item']] = s['keterangan']
        if s['tahun']==2025: it_rev25[s['item']] += s['jumlah']
        else: it_rev26[s['item']] += s['jumlah']
    top_items = sorted(it_rev.items(), key=lambda x: x[1], reverse=True)[:15]
    total_sku_25 = sum(1 for yrs in it_year.values() if 2025 in yrs)
    total_sku_26 = sum(1 for yrs in it_year.values() if 2026 in yrs)

    # Customers
    cu = defaultdict(float)
    cu_rev25 = defaultdict(float)
    cu_rev26 = defaultdict(float)
    cu_name = {}
    cu_groups = defaultdict(lambda: defaultdict(float))
    cu_groups_25 = defaultdict(lambda: defaultdict(float))
    cu_groups_26 = defaultdict(lambda: defaultdict(float))
    cu_qty = defaultdict(float)
    for s in filtered:
        if s['kode_pelanggan']:
            cu[s['kode_pelanggan']] += s['jumlah']
            cu_name[s['kode_pelanggan']] = s['pelanggan']
            cu_groups[s['kode_pelanggan']][s['grup_item']] += s['jumlah']
            cu_qty[s['kode_pelanggan']] += s['qty']
            if s['tahun']==2025:
                cu_rev25[s['kode_pelanggan']] += s['jumlah']
                cu_groups_25[s['kode_pelanggan']][s['grup_item']] += s['jumlah']
            else:
                cu_rev26[s['kode_pelanggan']] += s['jumlah']
                cu_groups_26[s['kode_pelanggan']][s['grup_item']] += s['jumlah']
    top_custs = sorted(cu.items(), key=lambda x: x[1], reverse=True)[:20]

    # LOB — year-aware
    lo = defaultdict(float)
    lo_25 = defaultdict(float)
    lo_26 = defaultdict(float)
    for s in filtered:
        lo[s['lob']] += s['jumlah']
        if s['tahun']==2025: lo_25[s['lob']] += s['jumlah']
        else: lo_26[s['lob']] += s['jumlah']
    lo_sorted = sorted(lo.items(), key=lambda x: x[1], reverse=True)
    lo_labels = [l[0] for l in lo_sorted]
    lo_values25 = [lo_25.get(l,0) for l in lo_labels]
    lo_values26 = [lo_26.get(l,0) for l in lo_labels]

    # Sales by person (per salesperson code)
    sp = defaultdict(lambda: {'revenue':0,'qty':0,'customers':set(),'cust25':set(),'cust26':set(),'rev25':0,'rev26':0,'qty25':0,'qty26':0,'cust_rev':defaultdict(float),'cust_rev25':defaultdict(float),'cust_rev26':defaultdict(float)})
    for s in filtered:
        if s['sales']:
            sp[s['sales']]['revenue'] += s['jumlah']
            sp[s['sales']]['qty'] += s['qty']
            if s['kode_pelanggan']:
                sp[s['sales']]['customers'].add(s['kode_pelanggan'])
                sp[s['sales']]['cust_rev'][s['kode_pelanggan']] += s['jumlah']
            if s['tahun']==2025:
                sp[s['sales']]['rev25'] += s['jumlah']
                sp[s['sales']]['qty25'] += s['qty']
                if s['kode_pelanggan']:
                    sp[s['sales']]['cust25'].add(s['kode_pelanggan'])
                    sp[s['sales']]['cust_rev25'][s['kode_pelanggan']] += s['jumlah']
            else:
                sp[s['sales']]['rev26'] += s['jumlah']
                sp[s['sales']]['qty26'] += s['qty']
                if s['kode_pelanggan']:
                    sp[s['sales']]['cust26'].add(s['kode_pelanggan'])
                    sp[s['sales']]['cust_rev26'][s['kode_pelanggan']] += s['jumlah']
    sp_list = [{'code':k,'revenue':v['revenue'],'qty':v['qty'],'customers':len(v['customers']),'cust25':len(v['cust25']),'cust26':len(v['cust26']),'rev25':v['rev25'],'rev26':v['rev26'],'qty25':v['qty25'],'qty26':v['qty26'],
        'cust_top':[{'kode':c,'nama':cu_name.get(c,''),'revenue':r,'revenue25':v['cust_rev25'].get(c,0),'revenue26':v['cust_rev26'].get(c,0)} for c,r in sorted(v['cust_rev'].items(), key=lambda x:-x[1])[:30]]} for k,v in sp.items()]
    sp_list.sort(key=lambda x: x['revenue'], reverse=True)

    return {
        'total25': total_25, 'total26': total_26,
        'monthly': {'labels': month_order, 'y2025': [monthly['2025'].get(m,0) for m in month_order], 'y2026': [monthly['2026'].get(m,0) for m in month_order]},
        'branches': {'labels':[b[0] for b in br_sorted],'rev25':[b[1]['rev25'] for b in br_sorted],'rev26':[b[1]['rev26'] for b in br_sorted]},
        'branch_monthly': {br_name: {m: {'rev25': br_monthly[br_name][m]['rev25'], 'rev26': br_monthly[br_name][m]['rev26']} for m in month_order} for br_name in br_monthly},
        'products': {'labels':[g[0] for g in gr_sorted],'values':[g[1] for g in gr_sorted],'classes':{g[0]:dict(sorted(gr_class.get(g[0],{}).items(), key=lambda x:x[1], reverse=True)) for g in gr_sorted},
            'values25':[gr_25.get(g[0],0) for g in gr_sorted],'values26':[gr_26.get(g[0],0) for g in gr_sorted],
            'classes25':{g[0]:dict(sorted(gr_class_25.get(g[0],{}).items(), key=lambda x:x[1], reverse=True)) for g in gr_sorted},
            'classes26':{g[0]:dict(sorted(gr_class_26.get(g[0],{}).items(), key=lambda x:x[1], reverse=True)) for g in gr_sorted},
            **({'classes_month':{g[0]:{m:{c:v for c,v in cls.items()} for m,cls in gr_class_month.get(g[0],{}).items()} for g in gr_sorted}} if class_month else {})},
        'items': [{'kode':i[0],'nama':it_name.get(i[0],i[0])[:40],'revenue':i[1],'qty':it_qty[i[0]],'rev25':it_rev25.get(i[0],0),'rev26':it_rev26.get(i[0],0)} for i in top_items],
        'total_sku': len(it_rev),
        'total_sku_25': total_sku_25,
        'total_sku_26': total_sku_26,
        'customers': [{'kode':c[0],'nama':cu_name.get(c[0],'')[:30],'revenue':c[1],'qty':cu_qty.get(c[0],0),'rev25':cu_rev25.get(c[0],0),'rev26':cu_rev26.get(c[0],0),'branch':branch or '',
            'groups':[{'group':g,'revenue':r,'rev25':cu_groups_25.get(c[0],{}).get(g,0),'rev26':cu_groups_26.get(c[0],{}).get(g,0)} for g,r in sorted(cu_groups.get(c[0],{}).items(), key=lambda x:-x[1])[:20]]} for c in top_custs],
        'lob': {'labels':lo_labels,'values':[l[1] for l in lo_sorted],'values25':lo_values25,'values26':lo_values26},
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

# Supplier → customer codes mapping (customers who bought supplier's items)
supplier_customers = defaultdict(set)
for s in sales:
    for sup, codes in supplier_items.items():
        if s['item'] in codes and s['kode_pelanggan']:
            supplier_customers[sup].add(s['kode_pelanggan'])

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
        # Also store per-branch-per-month customer revenue for this supplier
        sup_br_month_cust = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'revenue':0,'rev25':0,'rev26':0})))
        sup_cust_names = {}
        for s in sup_sales:
            if s['kode_pelanggan']:
                br, m, cu = s['cabang'], s['bulan'], s['kode_pelanggan']
                sup_br_month_cust[br][m][cu]['revenue'] += s['jumlah']
                if s['tahun']==2025: sup_br_month_cust[br][m][cu]['rev25'] += s['jumlah']
                else: sup_br_month_cust[br][m][cu]['rev26'] += s['jumlah']
                if s['pelanggan']: sup_cust_names[cu] = s['pelanggan'][:30]
        # Convert to serializable format
        sbmc = {}
        for br_name, months in sup_br_month_cust.items():
            sbmc[br_name] = {}
            for m_name, custs in months.items():
                cl = [{'kode':k,'nama':sup_cust_names.get(k,k),'revenue':v['revenue'],'rev25':v['rev25'],'rev26':v['rev26']} for k,v in custs.items()]
                cl.sort(key=lambda x: x['revenue'], reverse=True)
                sbmc[br_name][m_name] = cl
        if sbmc:
            supplier_branch_sp[sup + '_br_month_cust'] = sbmc
        # Also store per-branch-per-month items for this supplier
        sup_br_month_items = defaultdict(lambda: defaultdict(lambda: {'it_rev':defaultdict(float),'it_qty':defaultdict(float),'it_rev25':defaultdict(float),'it_rev26':defaultdict(float),'it_name':{}}))
        for s in sup_sales:
            br, m, it = s['cabang'], s['bulan'], s['item']
            d = sup_br_month_items[br][m]
            d['it_rev'][it] += s['jumlah']
            d['it_qty'][it] += s['qty']
            if s['keterangan']: d['it_name'][it] = s['keterangan']
            if s['tahun']==2025: d['it_rev25'][it] += s['jumlah']
            else: d['it_rev26'][it] += s['jumlah']
        sbmi = {}
        for br_name, months in sup_br_month_items.items():
            sbmi[br_name] = {}
            for m_name, d in months.items():
                items_list = [{'kode':k,'nama':d['it_name'].get(k,k)[:40],'revenue':d['it_rev'][k],'qty':d['it_qty'][k],'rev25':d['it_rev25'].get(k,0),'rev26':d['it_rev26'].get(k,0)} for k in d['it_rev']]
                items_list.sort(key=lambda x: x['revenue'], reverse=True)
                sbmi[br_name][m_name] = items_list
        if sbmi:
            supplier_branch_sp[sup + '_br_month_items'] = sbmi
        # Also store per-branch-per-month product group data for this supplier
        sup_br_month_prods = defaultdict(lambda: defaultdict(lambda: {'gr_rev':defaultdict(float),'gr_rev25':defaultdict(float),'gr_rev26':defaultdict(float),'gr_cls':defaultdict(lambda: defaultdict(float)),'gr_cls25':defaultdict(lambda: defaultdict(float)),'gr_cls26':defaultdict(lambda: defaultdict(float))}))
        for s in sup_sales:
            br, m, it = s['cabang'], s['bulan'], s['item']
            grp = s['grup_item']
            cls = item_class_map.get(it, '')
            d = sup_br_month_prods[br][m]
            d['gr_rev'][grp] += s['jumlah']
            if cls: d['gr_cls'][grp][cls] += s['jumlah']
            if s['tahun']==2025:
                d['gr_rev25'][grp] += s['jumlah']
                if cls: d['gr_cls25'][grp][cls] += s['jumlah']
            else:
                d['gr_rev26'][grp] += s['jumlah']
                if cls: d['gr_cls26'][grp][cls] += s['jumlah']
        sbmp = {}
        for br_name, months in sup_br_month_prods.items():
            sbmp[br_name] = {}
            for m_name, d in months.items():
                groups = sorted(d['gr_rev'].items(), key=lambda x: x[1], reverse=True)
                sbmp[br_name][m_name] = {
                    'labels': [g[0] for g in groups],
                    'values': [d['gr_rev'][g[0]] for g in groups],
                    'values25': [d['gr_rev25'].get(g[0],0) for g in groups],
                    'values26': [d['gr_rev26'].get(g[0],0) for g in groups],
                    'classes': {g[0]: dict(sorted(d['gr_cls'].get(g[0],{}).items(), key=lambda x:x[1], reverse=True)) for g in groups},
                    'classes25': {g[0]: dict(sorted(d['gr_cls25'].get(g[0],{}).items(), key=lambda x:x[1], reverse=True)) for g in groups},
                    'classes26': {g[0]: dict(sorted(d['gr_cls26'].get(g[0],{}).items(), key=lambda x:x[1], reverse=True)) for g in groups},
                }
        if sbmp:
            supplier_branch_sp[sup + '_br_month_products'] = sbmp

# Pre-compute per-supplier-per-branch sales cache
# Only for branch+supplier combos that have data
supplier_branch_cache = {}
for sup in all_suppliers:
    sup_codes = supplier_items.get(sup, set())
    if not sup_codes:
        continue
    # Find which branches have sales for this supplier's items
    sup_branches = set(s['cabang'] for s in sales if s['item'] in sup_codes and s['cabang'])
    if sup_branches:
        supplier_branch_cache[sup] = {}
        for br in sup_branches:
            supplier_branch_cache[sup][br] = agg_sales(branch=br, supplier=sup)

# ============================================================
# GROUP ITEM CACHES (for sales tab group filter)
# ============================================================
# Collect all unique group codes from sales data
all_groups = sorted(set(s['grup_item'] for s in sales if s['grup_item']))

# Group → item codes mapping
group_items = defaultdict(set)
for s in sales:
    if s['grup_item'] and s['item']:
        group_items[s['grup_item']].add(s['item'])

# Pre-compute per-group sales caches
group_sales_cache = {}
for grp in all_groups:
    group_sales_cache[grp] = agg_sales(group=grp, class_month=True)

print(f"  Group cache: {len(group_sales_cache)} groups")

# Per-group per-branch per-month items & customers (for accurate Top Item / Top Customer
# when Group + Branch (+ Month) filters are active). Compact array format to save space.
# items: [kode, nama, revenue, qty, rev25, rev26]  | custs: [kode, nama, revenue, rev25, rev26]
g_bm_items = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'rev':defaultdict(float),'qty':defaultdict(float),'r25':defaultdict(float),'r26':defaultdict(float),'nm':{}})))
g_bm_cust  = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'rev':defaultdict(float),'r25':defaultdict(float),'r26':defaultdict(float),'nm':{}})))
for s in sales:
    grp = s['grup_item']
    if not grp: continue
    br, m = s['cabang'], s['bulan']
    it = s['item']
    di = g_bm_items[grp][br][m]
    di['rev'][it] += s['jumlah']; di['qty'][it] += s['qty']
    if s['keterangan']: di['nm'][it] = s['keterangan'][:40]
    if s['tahun']==2025: di['r25'][it] += s['jumlah']
    else: di['r26'][it] += s['jumlah']
    if s['kode_pelanggan']:
        cu = s['kode_pelanggan']
        dc = g_bm_cust[grp][br][m]
        dc['rev'][cu] += s['jumlah']
        if s['pelanggan']: dc['nm'][cu] = s['pelanggan'][:30]
        if s['tahun']==2025: dc['r25'][cu] += s['jumlah']
        else: dc['r26'][cu] += s['jumlah']

def _ser_gbm_items(g):
    out = {}
    for grp, brs in g.items():
        out[grp] = {}
        for br, mos in brs.items():
            out[grp][br] = {}
            for m, d in mos.items():
                rows = [[k, d['nm'].get(k, k), round(d['rev'][k]), round(d['qty'][k]), round(d['r25'].get(k,0)), round(d['r26'].get(k,0))] for k in d['rev']]
                rows.sort(key=lambda x: x[2], reverse=True)
                out[grp][br][m] = rows
    return out

def _ser_gbm_cust(g):
    out = {}
    for grp, brs in g.items():
        out[grp] = {}
        for br, mos in brs.items():
            out[grp][br] = {}
            for m, d in mos.items():
                rows = [[k, d['nm'].get(k, k), round(d['rev'][k]), round(d['r25'].get(k,0)), round(d['r26'].get(k,0))] for k in d['rev']]
                rows.sort(key=lambda x: x[2], reverse=True)
                out[grp][br][m] = rows
    return out

group_br_month_items = _ser_gbm_items(g_bm_items)
group_br_month_cust  = _ser_gbm_cust(g_bm_cust)
print(f"  Group br-month items/cust cache built")

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

def _parse_stock_month(tanggal):
    """Parse stock date to 3-letter month: '31 January 2026' -> 'Jan', '28-Feb' -> 'Feb'"""
    # Handle '31-Jan' format
    if '-' in tanggal:
        return tanggal.split('-')[1]
    # Handle '31 January 2026' format
    month_map = {'January':'Jan','February':'Feb','March':'Mar','April':'Apr','May':'May','June':'Jun',
                 'July':'Jul','August':'Aug','September':'Sep','October':'Oct','November':'Nov','December':'Dec'}
    parts = tanggal.split()
    if len(parts) >= 2:
        m = parts[1].strip()
        return month_map.get(m, m[:3])
    return tanggal

# ============================================================
# STOCK aggregation with filters
# ============================================================
def agg_stock(branch=None, months=None):
    filtered = stock
    if branch:
        filtered = [s for s in filtered if s['cabang'] == branch]
    if months:
        month_set = set(months)
        filtered = [s for s in filtered if _parse_stock_month(s['tanggal']) in month_set]

    by_branch = defaultdict(lambda: {'items':0,'akhir':0,'in':0,'out':0,'nilai':0})
    by_item = defaultdict(lambda: {'akhir':0,'in':0,'out':0,'nama':''})
    by_group_nilai = defaultdict(float)
    active_items = set()
    nilai_aktif = 0
    nilai_stagnant = 0
    for s in filtered:
        b = by_branch[s['cabang']]; b['items']+=1; b['akhir']+=s['akhir']; b['in']+=s['in']; b['out']+=s['out']; b['nilai']+=s['nilai']
        si = by_item[s['item_code']]; si['akhir']+=s['akhir']; si['in']+=s['in']; si['out']+=s['out']; si['nama']=s['nama']
        # Group by group_name for stock value
        code = s['item_code']
        grp = item_map.get(code, {}).get('group', '')
        if grp:
            grp_name = group_name_map.get(grp, grp)
        else:
            grp_name = '(Tanpa Group)'
        by_group_nilai[grp_name] += s['nilai']
        if s['out'] > 0:
            active_items.add(s['item_code'])
            nilai_aktif += s['nilai']
        else:
            nilai_stagnant += s['nilai']

    br_sorted = sorted(by_branch.items(), key=lambda x: x[1]['nilai'], reverse=True)
    top_items = sorted(by_item.items(), key=lambda x: x[1]['akhir'], reverse=True)[:20]
    top_groups = sorted(by_group_nilai.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        'branches': {'labels':[b[0] for b in br_sorted],'items':[b[1]['items'] for b in br_sorted],'akhir':[b[1]['akhir'] for b in br_sorted],'masuk':[b[1]['in'] for b in br_sorted],'keluar':[b[1]['out'] for b in br_sorted],'nilai':[b[1]['nilai'] for b in br_sorted]},
        'items': [{'item':s[0],'nama':s[1]['nama'][:40],'akhir':s[1]['akhir'],'masuk':s[1]['in'],'keluar':s[1]['out']} for s in top_items],
        'nilai_by_group': [{'group': g, 'nilai': n} for g, n in top_groups],
        'active_count': len(active_items),
        'active_items': list(active_items),
        'nilai_aktif': nilai_aktif,
        'nilai_stagnant': nilai_stagnant,
    }

default_stock = agg_stock()

# Pre-compute per-branch stock caches
branch_stock_cache = {}
for br in all_branches:
    branch_stock_cache[br] = agg_stock(branch=br)

# Pre-compute per-month stock caches (for month filter)
stock_month_set = set()
for s in stock:
    m = _parse_stock_month(s['tanggal'])
    stock_month_set.add(m)

stock_month_cache = {}
for m in stock_month_set:
    stock_month_cache[m] = agg_stock(months=[m])

# Pre-compute per-branch-per-month stock caches
branch_month_stock_cache = {}
for br in all_branches:
    branch_month_stock_cache[br] = {}
    for m in stock_month_set:
        branch_month_stock_cache[br][m] = agg_stock(branch=br, months=[m])

# --- branch_stagnant_6m: nilai item yang TIDAK terjual dalam 6 bulan ---
# Build sold-items index: {(branch, month, year): set(item_codes)}
branch_month_sold = defaultdict(set)
for s in sales:
    branch_month_sold[(s['cabang'], s['bulan'], s['tahun'])].add(s['item'])

MONTH_LIST = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
branch_stagnant_6m = {}
branch_stagnant_items = {}
for br in all_branches:
    branch_stagnant_6m[br] = {}
    branch_stagnant_items[br] = {}
    for m in stock_month_set:
        mi = MONTH_LIST.index(m)
        # 6-month sales window before selected month
        window = []
        for off in range(1, 7):
            idx = mi - off
            yr = 2026
            if idx < 0: idx += 12; yr -= 1
            window.append((MONTH_LIST[idx], yr))
        # All items sold in this window across both years
        sold_6m = set()
        for (wm, wy) in window:
            sold_6m |= branch_month_sold.get((br, wm, wy), set())
        # Sum nilai for stock items NOT sold in window + collect detail
        filtered = [s for s in stock if s['cabang'] == br and _parse_stock_month(s['tanggal']) == m]
        stagnant_items = []
        stagnant_by_item = defaultdict(float)
        stagnant_by_qty = defaultdict(float)
        stagnant_by_nama = {}
        for s in filtered:
            if s['item_code'] not in sold_6m and s['nilai'] > 0:
                stagnant_by_item[s['item_code']] += s['nilai']
                stagnant_by_qty[s['item_code']] += s['akhir']
                stagnant_by_nama[s['item_code']] = s['nama']
        stagnant_nilai = sum(stagnant_by_item.values())
        branch_stagnant_6m[br][m] = stagnant_nilai
        # Store detail items for modal (aggregated by item_code)
        for ic, n in sorted(stagnant_by_item.items(), key=lambda x: -x[1]):
            stagnant_items.append({
                'item_code': ic,
                'nama': stagnant_by_nama.get(ic, ''),
                'nilai': n,
                'qty': round(stagnant_by_qty[ic], 2),
            })
        branch_stagnant_items[br][m] = stagnant_items

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
    'stock_active': len([si for si in stock_by_item.values() if si['out'] > 0]),
    'stock_nilai_total': stock_nilai_total,
    'stock_nilai_top_groups': [{'group': g, 'nilai': n} for g, n in stock_nilai_top_groups],
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
supplier_customers_map = {k: list(v) for k, v in supplier_customers.items()}

dashboard = {
    'filters': {
        'branches': all_branches,
        'months': all_months,
        'suppliers': all_suppliers,
        'supplier_items': supplier_items_map,
        'supplier_customers': supplier_customers_map,
        'groups': all_groups,
        'group_items': {k: list(v) for k, v in group_items.items()},
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
    'supplier_branch_cache': supplier_branch_cache,
    'group_cache': group_sales_cache,
    'group_br_month_items': group_br_month_items,
    'group_br_month_cust': group_br_month_cust,
    'branch_stock_cache': branch_stock_cache,
    'stock_month_cache': stock_month_cache,
    'branch_month_stock_cache': branch_month_stock_cache,
    'branch_stagnant_6m': branch_stagnant_6m,
    'branch_stagnant_items': branch_stagnant_items,
}

out_path = os.environ.get('OUT_PATH', '/tmp/dashboard_data_pg.json')
with open(out_path, 'w') as f:
    json.dump(dashboard, f)

size = os.path.getsize(out_path)
print(f"\n✅ Dashboard JSON: {size:,} bytes ({size/1024:.0f} KB)")
print(f"Filters: {len(all_branches)} branches, {len(all_months)} months, {len(all_suppliers)} suppliers, {len(all_groups)} groups")
print(f"Sales: {len(sales)} rows")
print(f"Branch cache: {len(branch_sales_cache)} entries")
print(f"Month cache: {len(month_sales_cache)} entries")
print(f"Group cache: {len(group_sales_cache)} entries")
