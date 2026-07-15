#!/bin/bash
# Refresh data dari PostgreSQL VPS (Jalur A) + deploy JSON ke Vercel.
# Sumber: sales+stock+produk+customer dari PostgreSQL. Master + procurement dari file lokal.
set -e
cd /root/projects/sna-dashboard

VPS=root@43.134.103.128
export SSHPASS="$(cat ~/.hermes/secrets/vps_root_password)"

echo "📥 Export data dari PostgreSQL VPS..."
cat > /tmp/pg_export_remote.sh <<'REMOTE'
#!/bin/bash
PSQL="psql -h 127.0.0.1 -U sna_dashboard -d sna_sales"
$PSQL -c "\copy (SELECT nomor_invoice,tanggal,kode_cabang,kode_customer,kode_item,qty,harga,diskon,jumlah,total,status,sales,delivery,non_sales,bulan,lob FROM fact_penjualan) TO '/tmp/pg_sales.csv' WITH CSV HEADER"
$PSQL -c "\copy (SELECT kode_cabang,kode_item,nama_item,qty_awal,qty_masuk,qty_keluar,qty_akhir,periode,wh,tanggal,nilai_stok,hrg_kirim,hrg_ambil FROM fact_stok) TO '/tmp/pg_stock.csv' WITH CSV HEADER"
$PSQL -c "\copy (SELECT kode_item,nama_item,grup_item,kategori_item,item_jp,satuan,kode_supplier,brand,supplier_name FROM dim_produk) TO '/tmp/pg_produk.csv' WITH CSV HEADER"
$PSQL -c "\copy (SELECT kode_customer,nama_customer FROM dim_customer) TO '/tmp/pg_customer.csv' WITH CSV HEADER"
REMOTE
sshpass -e scp -o StrictHostKeyChecking=no /tmp/pg_export_remote.sh $VPS:/tmp/pg_export_remote.sh
sshpass -e ssh -o StrictHostKeyChecking=no $VPS 'bash /tmp/pg_export_remote.sh'
for f in pg_sales pg_stock pg_produk pg_customer; do
  sshpass -e scp -o StrictHostKeyChecking=no $VPS:/tmp/$f.csv /tmp/$f.csv
done

echo "⚙️  Generate dashboard_data.json dari PostgreSQL..."
OUT_PATH=/root/projects/sna-dashboard/dashboard_data.json python3 /root/projects/sna-dashboard/fetch_data_pg.py

echo "🚀 Deploying ke Vercel..."
vercel --prod --yes --token "$(cat ~/.hermes/secrets/vercel_token)"

echo ""
echo "✅ Dashboard data updated dari PostgreSQL: https://sna-dashboard-rouge.vercel.app"
