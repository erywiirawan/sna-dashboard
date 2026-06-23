#!/usr/bin/env python3
"""Embed encrypted dashboard_data.json into index.html with AES-256-GCM."""
import json, re, os, base64, hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

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
    print(f'   Default password: {password}')

# Load JSON data
with open(os.path.join(DASHBOARD_DIR, 'dashboard_data.json')) as f:
    data = json.load(f)

json_bytes = json.dumps(data, separators=(',', ':')).encode('utf-8')

# Encrypt with AES-256-GCM
salt = os.urandom(16)
iv = os.urandom(12)

kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=100000,
)
key = kdf.derive(password.encode('utf-8'))

aesgcm = AESGCM(key)
ciphertext = aesgcm.encrypt(iv, json_bytes, None)

# Pack: salt(16) + iv(12) + ciphertext
encrypted = salt + iv + ciphertext
encrypted_b64 = base64.b64encode(encrypted).decode('ascii')

# Read HTML template
with open(os.path.join(DASHBOARD_DIR, 'index.html')) as f:
    html = f.read()

# Replace `const DATA = {...};` with encrypted version
html = re.sub(
    r'const DATA = \{.*?\};',
    f'const ENCRYPTED_DATA = "{encrypted_b64}";\nlet DATA = null;',
    html,
    count=1,
    flags=re.DOTALL
)

# Replace `applyFilters();` at the end with password gate
old_init = """applyFilters();"""
new_init = """async function deriveKey(password, salt) {
    const enc = new TextEncoder();
    const keyMaterial = await crypto.subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveKey']);
    return crypto.subtle.deriveKey({name:'PBKDF2',salt,iterations:100000,hash:'SHA-256'}, keyMaterial, {name:'AES-GCM',length:256}, false, ['decrypt']);
}

async function decryptData(password) {
    const raw = Uint8Array.from(atob(ENCRYPTED_DATA), c => c.charCodeAt(0));
    const salt = raw.slice(0, 16);
    const iv = raw.slice(16, 28);
    const ciphertext = raw.slice(28);
    const key = await deriveKey(password, salt);
    const decrypted = await crypto.subtle.decrypt({name:'AES-GCM', iv}, key, ciphertext);
    return JSON.parse(new TextDecoder().decode(decrypted));
}

async function tryLogin() {
    const pw = document.getElementById('pwInput').value;
    const err = document.getElementById('pwError');
    const btn = document.getElementById('pwBtn');
    const prog = document.getElementById('pwProgress');
    err.style.display = 'none';
    btn.disabled = true;
    btn.textContent = 'Mendekripsi...';
    prog.style.display = 'block';
    try {
        DATA = await decryptData(pw);
        document.getElementById('authOverlay').style.display = 'none';
        document.getElementById('app').style.display = '';
        applyFilters();
    } catch(e) {
        err.textContent = 'Password salah!';
        err.style.display = 'block';
        btn.disabled = false;
        btn.textContent = 'Masuk';
        prog.style.display = 'none';
    }
}

document.getElementById('pwInput').addEventListener('keydown', e => { if(e.key==='Enter') tryLogin(); });
"""
html = html.replace(old_init, new_init)

# Add auth overlay HTML before </body>
auth_overlay = """
<div id="authOverlay" style="position:fixed;top:0;left:0;width:100%;height:100%;background:#0f172a;z-index:99999;display:flex;align-items:center;justify-content:center">
  <div style="text-align:center;padding:40px;background:#1e293b;border-radius:16px;border:1px solid #334155;max-width:380px;width:90%">
    <div style="font-size:48px;margin-bottom:16px">🔒</div>
    <h2 style="color:#f1f5f9;margin:0 0 8px;font-size:20px">PT SNA Dashboard</h2>
    <p style="color:#94a3b8;margin:0 0 24px;font-size:13px">Masukkan password untuk mengakses dashboard</p>
    <input id="pwInput" type="password" placeholder="Password" style="width:100%;padding:12px 16px;background:#0f172a;border:1px solid #475569;border-radius:8px;color:#f1f5f9;font-size:14px;outline:none;box-sizing:border-box" autofocus>
    <p id="pwError" style="color:#ef4444;font-size:12px;margin:8px 0 0;display:none"></p>
    <div id="pwProgress" style="display:none;margin-top:16px">
      <div style="width:100%;height:4px;background:#334155;border-radius:2px;overflow:hidden">
        <div style="width:100%;height:100%;background:#3b82f6;animation:pwload 2s ease-in-out infinite"></div>
      </div>
      <p style="color:#94a3b8;font-size:11px;margin:8px 0 0">Mendekripsi data...</p>
    </div>
    <button id="pwBtn" onclick="tryLogin()" style="margin-top:16px;width:100%;padding:12px;background:#3b82f6;color:white;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer">Masuk</button>
  </div>
</div>
<style>@keyframes pwload{0%{transform:translateX(-100%)}50%{transform:translateX(0)}100%{transform:translateX(100%)}}</style>
"""

# Insert auth overlay and app wrapper
# Structure: <body> <div id="app" style="display:none"> ...content... </div> <authOverlay> </body>
# Find the <body> tag and wrap content
body_idx = html.find('<body>')
if body_idx >= 0:
    # Insert app div opening right after <body>
    html = html[:body_idx+6] + '\n<div id="app" style="display:none">' + html[body_idx+6:]

# Insert closing app div + auth overlay before </body>
close_body_idx = html.rfind('</body>')
if close_body_idx >= 0:
    closing = '\n</div><!-- /app -->\n' + auth_overlay + '\n'
    html = html[:close_body_idx] + closing + html[close_body_idx:]

with open(os.path.join(DASHBOARD_DIR, 'index.html'), 'w') as f:
    f.write(html)

print(f'✅ Encrypted {len(json_bytes):,} bytes → {len(encrypted_b64):,} bytes (AES-256-GCM)')
print(f'   Password: {password}')
print(f'   Change password: edit {PASSWORD_FILE}')
