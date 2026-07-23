#!/bin/bash
# Dijalankan DI VPS oleh webhook. Export PG lokal → generate JSON → deploy Vercel.
# Tidak perlu self-SSH (psql langsung ke localhost via .pgpass).
set -e
cd /root/projects/sna-dashboard
export PGPASSFILE=/root/.pgpass
PSQL="psql -h 127.0.0.1 -U sna_dashboard -d sna_sales"

echo "[$(date '+%F %T')] Export data dari PostgreSQL (lokal)..."
$PSQL -c "\copy (SELECT nomor_invoice,tanggal,kode_cabang,kode_customer,kode_item,qty,harga,diskon,jumlah,total,status,sales,delivery,non_sales,bulan,lob FROM fact_penjualan) TO '/tmp/pg_sales.csv' WITH CSV HEADER"
$PSQL -c "\copy (SELECT kode_cabang,kode_item,nama_item,qty_awal,qty_masuk,qty_keluar,qty_akhir,periode,wh,tanggal,nilai_stok,hrg_kirim,hrg_ambil FROM fact_stok) TO '/tmp/pg_stock.csv' WITH CSV HEADER"
$PSQL -c "\copy (SELECT kode_item,nama_item,grup_item,kategori_item,item_jp,satuan,kode_supplier,brand,supplier_name FROM dim_produk) TO '/tmp/pg_produk.csv' WITH CSV HEADER"
$PSQL -c "\copy (SELECT kode_customer,nama_customer FROM dim_customer) TO '/tmp/pg_customer.csv' WITH CSV HEADER"
$PSQL -c "\copy (SELECT kode,nama_barang,satuan,group_code,group_name,class_code,class_name,type_code,supplier FROM dim_master_item) TO '/tmp/pg_master.csv' WITH CSV HEADER"
$PSQL -c "\copy (SELECT status,reg,cab,po,kode,nama,kategori,supplier,qty_po,nilai_beli,tgl_po,total_berat FROM fact_procurement) TO '/tmp/pg_procurement.csv' WITH CSV HEADER"
$PSQL -c "\copy (SELECT kode_cabang,nama_cabang,regional,area FROM dim_cabang) TO '/tmp/pg_cabang.csv' WITH CSV HEADER"

echo "[$(date '+%F %T')] Generate dashboard_data.json..."
PG_DIR=/tmp OUT_PATH=/root/projects/sna-dashboard/dashboard_data.json /usr/bin/python3 /root/projects/sna-dashboard/fetch_data_pg.py

echo "[$(date '+%F %T')] Deploy ke Vercel..."
export PATH=/root/.hermes/node/bin:$PATH
/root/.hermes/node/bin/vercel --prod --yes --token "$(cat /root/.hermes/secrets/vercel_token)" >/tmp/refresh_deploy.log 2>&1

echo "[$(date '+%F %T')] Selesai. Dashboard updated."
