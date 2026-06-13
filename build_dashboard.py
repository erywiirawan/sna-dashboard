#!/usr/bin/env python3
"""Embed dashboard_data.json into index.html as inline DATA const."""
import json, re

with open('/root/sna-dashboard/dashboard_data.json') as f:
    data = json.load(f)

with open('/root/sna-dashboard/index.html') as f:
    html = f.read()

json_str = json.dumps(data, separators=(',', ':'))

html = re.sub(
    r'const DATA = \{.*?\};',
    'const DATA = ' + json_str + ';',
    html,
    count=1,
    flags=re.DOTALL
)

with open('/root/sna-dashboard/index.html', 'w') as f:
    f.write(html)

print(f'✅ Embedded {len(json_str):,} bytes of JSON into index.html')
