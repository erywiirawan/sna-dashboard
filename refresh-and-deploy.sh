#!/bin/bash
# Refresh data dari Google Sheets + deploy JSON
set -e
echo "📥 Fetching data dari Google Sheets..."
python3 /root/sna-dashboard/fetch_data.py

echo "🚀 Deploying ke Vercel..."
cd /root/sna-dashboard
vercel --prod --yes --token $(cat ~/.hermes/secrets/vercel_token)

echo ""
echo "✅ Dashboard data updated: https://sna-dashboard-rouge.vercel.app"
