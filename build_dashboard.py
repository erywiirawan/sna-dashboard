#!/usr/bin/env python3
"""Embed dashboard_data.json into index.html with password protection."""
import json, re, os, hashlib

DASHBOARD_DIR = '/root/sna-dashboard'
PASSWORD_FILE = os.path.join(DASHBOARD_DIR, '.dashboard_password')

# Load or create password
if os.path.exists(PASSWORD_FILE):
    with open(PASSWORD_FILE) as f:
        password = f.read().strip()
else:
    password = 'sna2026'
    with open(PASSWORD_FILE, 'w') as f:
        f.write(password)
    os.chmod(PASSWORD_FILE, 0o600)
    print(f'⚠️  Created default password file: {PASSWORD_FILE}')

pw_hash = hashlib.sha256(password.encode()).hexdigest()

# Load JSON data
with open(os.path.join(DASHBOARD_DIR, 'dashboard_data.json')) as f:
    data = json.load(f)

json_str = json.dumps(data, separators=(',', ':'))
json_bytes = json_str.encode('utf-8')

# Read HTML template
with open(os.path.join(DASHBOARD_DIR, 'index.html')) as f:
    html = f.read()

# Remove existing password gate if present (from previous build)
if '<!-- Password Gate -->' in html:
    gate_start = html.rfind('<!-- Password Gate -->')
    # Find the matching closing </div> for the overlay
    overlay_end = html.find('</div><!-- /app -->', gate_start)
    if overlay_end >= 0:
        html = html[:gate_start] + html[overlay_end + len('</div><!-- /app -->'):]

# Remove existing app wrapper if present
html = html.replace('<div id="app" style="display:none">', '', 1)
# Remove the matching closing </div><!-- /app --> if still present
html = html.replace('</div><!-- /app -->', '', 1)

# Inject password gate HTML before </body>
password_gate = """
<!-- Password Gate -->
<div id="authOverlay" style="position:fixed;top:0;left:0;width:100%;height:100%;background:#0f172a;z-index:99999;display:flex;align-items:center;justify-content:center">
  <div style="text-align:center;padding:40px;background:#1e293b;border-radius:16px;border:1px solid #334155;max-width:380px;width:90%">
    <div style="font-size:48px;margin-bottom:16px">🔒</div>
    <h2 style="color:#f1f5f9;margin:0 0 8px;font-size:20px">PT SNA Dashboard</h2>
    <p style="color:#94a3b8;margin:0 0 24px;font-size:13px">Masukkan password untuk mengakses dashboard</p>
    <input id="pwInput" type="password" placeholder="Password" style="width:100%;padding:12px 16px;background:#0f172a;border:1px solid #475569;border-radius:8px;color:#f1f5f9;font-size:14px;outline:none;box-sizing:border-box" autofocus>
    <p id="pwError" style="color:#ef4444;font-size:12px;margin:8px 0 0;display:none"></p>
    <button id="pwBtn" onclick="tryLogin()" style="margin-top:16px;width:100%;padding:12px;background:#3b82f6;color:white;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer">Masuk</button>
  </div>
</div>
<script>
async function sha256(str) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(str));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2,'0')).join('');
}
const PW_HASH = '__PW_HASH__';
async function tryLogin() {
  const pw = document.getElementById('pwInput').value;
  const err = document.getElementById('pwError');
  const btn = document.getElementById('pwBtn');
  err.style.display = 'none';
  btn.disabled = true;
  btn.textContent = 'Memeriksa...';
  const hash = await sha256(pw);
  if (hash === PW_HASH) {
    document.getElementById('authOverlay').style.display = 'none';
    document.getElementById('app').style.display = '';
  } else {
    err.textContent = 'Password salah!';
    err.style.display = 'block';
    btn.disabled = false;
    btn.textContent = 'Masuk';
  }
}
document.getElementById('pwInput').addEventListener('keydown', e => { if(e.key==='Enter') tryLogin(); });
document.getElementById('app').style.display = 'none';
</script>
"""

password_gate = password_gate.replace('__PW_HASH__', pw_hash)

# Wrap body content in div#app and add password gate
body_tag = '<body>'
idx = html.find(body_tag)
if idx >= 0:
    html = html[:idx + len(body_tag)] + '<div id="app" style="display:none">' + html[idx + len(body_tag):]

close_body = '</body>'
idx2 = html.rfind(close_body)
if idx2 >= 0:
    html = html[:idx2] + '</div><!-- /app -->\n' + password_gate + close_body + html[idx2 + len(close_body):]

with open(os.path.join(DASHBOARD_DIR, 'index.html'), 'w') as f:
    f.write(html)

print(f'✅ Embedded {len(json_bytes):,} bytes of JSON + password gate')
print(f'   Password: {password}')
print(f'   Change password: edit {PASSWORD_FILE}')
