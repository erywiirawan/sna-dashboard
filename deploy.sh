#!/bin/bash
# Deploy SNA Dashboard ke Vercel (HTML + JSON)
set -e
cd /root/sna-dashboard
echo "🚀 Deploying SNA Dashboard..."
vercel --prod --yes --token $(cat ~/.hermes/secrets/vercel_token)
echo ""
echo "✅ Deployed: https://sna-dashboard-rouge.vercel.app"
