"""Build the public, password-protected copy of the dashboard for GitHub Pages (docs/).

  .venv/bin/python -I scripts/build_site.py            # app/ -> docs/ (data encrypted)
  .venv/bin/python -I scripts/build_site.py --new-password

The page code, fonts, map library and sketch thumbnails are published as they are. app/data.json (all lots,
valuations and bid caps) is gzip-compressed and encrypted with AES-256-GCM; the key is derived from the site
password with PBKDF2-SHA256. The browser decrypts it with WebCrypto after the password is typed (app.js).
The password and the salt live in .secrets/ (git-ignored); the salt stays fixed so a device that chose
«remember me» keeps working after every update, until the password is changed.
"""
import base64
import gzip
import json
import os
import secrets
import shutil
import sys

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

APP, OUT, SEC = 'app', 'docs', '.secrets'
ITER = 310_000
PW_FILE, SALT_FILE = os.path.join(SEC, 'site_password.txt'), os.path.join(SEC, 'site_salt.b64')


def new_password():
    words = [w.strip().lower() for w in open('/usr/share/dict/words') if 4 <= len(w.strip()) <= 6 and w.strip().isalpha()
             and w.strip().islower()]
    pw = '-'.join(secrets.choice(words) for _ in range(3)) + '-' + str(secrets.randbelow(90) + 10)
    os.makedirs(SEC, exist_ok=True)
    with open(PW_FILE, 'w') as f:
        f.write(pw + '\n')
    with open(SALT_FILE, 'w') as f:
        f.write(base64.b64encode(secrets.token_bytes(16)).decode() + '\n')
    os.chmod(PW_FILE, 0o600)
    print('new site password written to', PW_FILE)


def b64(b):
    return base64.b64encode(b).decode()


def main():
    if '--new-password' in sys.argv or not os.path.exists(PW_FILE):
        new_password()
    pw = open(PW_FILE).read().strip()
    salt = base64.b64decode(open(SALT_FILE).read().strip())
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(pw.encode())

    # copy the static app (everything except the plain data and the local per-user state)
    if os.path.exists(OUT):
        for name in os.listdir(OUT):
            if name == 'img':
                continue                          # thumbnails are synced below, not recopied every time
            p = os.path.join(OUT, name)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(OUT, exist_ok=True)
    for name in os.listdir(APP):
        src = os.path.join(APP, name)
        if name in ('data.json', 'state', 'img') or name.startswith('.'):
            continue
        dst = os.path.join(OUT, name)
        shutil.copytree(src, dst) if os.path.isdir(src) else shutil.copy2(src, dst)
    os.makedirs(os.path.join(OUT, 'img'), exist_ok=True)
    have = set(os.listdir(os.path.join(OUT, 'img')))
    for name in os.listdir(os.path.join(APP, 'img')):
        if name not in have:
            shutil.copy2(os.path.join(APP, 'img', name), os.path.join(OUT, 'img', name))

    raw = open(os.path.join(APP, 'data.json'), 'rb').read()
    iv = secrets.token_bytes(12)
    ct = AESGCM(key).encrypt(iv, gzip.compress(raw, 9), None)
    meta = json.load(open(os.path.join(APP, 'data.json'), encoding='utf-8'))['meta']
    json.dump(dict(v=1, kdf='PBKDF2-SHA256', iter=ITER, salt=b64(salt), iv=b64(iv), z='gzip', ct=b64(ct),
                   stamp=meta.get('updated_iso')), open(os.path.join(OUT, 'data.enc'), 'w'))
    open(os.path.join(OUT, '.nojekyll'), 'w').close()
    print(f"docs/: data {len(raw) // 1024} KB -> encrypted {len(ct) // 1024} KB, "
          f"{len(os.listdir(os.path.join(OUT, 'img')))} thumbnails, stamp {meta.get('updated_iso')}")


if __name__ == '__main__':
    main()
