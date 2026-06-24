#!/usr/bin/env python3
"""Update password hash in index.html (data is now fetched separately)."""
import hashlib, os

DASHBOARD_DIR = '/root/sna-dashboard'
PASSWORD_FILE = os.path.join(DASHBOARD_DIR, '.dashboard_password')

if os.path.exists(PASSWORD_FILE):
    with open(PASSWORD_FILE) as f:
        password = f.read().strip()
else:
    password = 'Izinkanmasuk24'
    with open(PASSWORD_FILE, 'w') as f:
        f.write(password)
    os.chmod(PASSWORD_FILE, 0o600)

pw_hash = hashlib.sha256(password.encode()).hexdigest()

with open(os.path.join(DASHBOARD_DIR, 'index.html')) as f:
    html = f.read()

# Update hash if needed
old_hash = "471f0338eb3c2dbb0abc3049a6e9eeb2bbae074e6f08b4de274e03e3dd46b71a"
if old_hash in html:
    html = html.replace(old_hash, pw_hash)
    with open(os.path.join(DASHBOARD_DIR, 'index.html'), 'w') as f:
        f.write(html)
    print(f"✅ Password hash updated")
else:
    print(f"ℹ️  Hash already current")

print(f"Password: {password}")
print(f"To change: edit {PASSWORD_FILE} then run this script")
