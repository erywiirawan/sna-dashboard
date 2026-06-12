#!/bin/bash
# Deploy SNA Dashboard ke Vercel
# Usage: bash /root/sna-dashboard/deploy.sh

set -e
cd /root/sna-dashboard
echo "Deploying SNA Dashboard..."
vercel --prod --yes --token $(cat ~/.hermes/secrets/vercel_token)
echo ""
echo "✅ Deployed: https://sna-dashboard-rouge.vercel.app"
