#!/bin/bash
# Refresh data dari Google Sheets + rebuild dashboard + deploy
# Usage: bash /root/sna-dashboard/refresh-and-deploy.sh

set -e
echo "📥 Fetching data dari Google Sheets..."
python3 /root/sna-dashboard/fetch_data.py

echo "🔨 Building dashboard..."
python3 /root/sna-dashboard/build_dashboard.py

echo "🚀 Deploying ke Vercel..."
cd /root/sna-dashboard
vercel --prod --yes --token $(cat ~/.hermes/secrets/vercel_token)

echo ""
echo "✅ Dashboard updated: https://sna-dashboard-rouge.vercel.app"
