#!/bin/bash
# Refresh data dari PostgreSQL + deploy JSON ke Vercel.
# Alias ke jalur PG (refresh-vps-local.sh). JANGAN pakai fetch_data.py (Sheets)
# karena tidak emit filters.groups / group_cache → dropdown Group Item kosong.
set -e
bash /root/projects/sna-dashboard/refresh-vps-local.sh
