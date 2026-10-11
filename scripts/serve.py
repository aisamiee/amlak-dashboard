"""Local server for the auction dashboard (stdlib only).

  .venv/bin/python -I scripts/serve.py [port]      -> http://127.0.0.1:8765/

Serves app/ as static files, the original sketch scans under /orig/, and a tiny JSON API for the
viewer's own state (watchlist, notes, bids) kept in app/state/user.json:
  GET  /api/state            -> {"items": {key: {...}}}
  PUT  /api/state/<key>      body: JSON object (or null to delete)
  GET  /api/version          -> {"updated_iso": ..., "mtime": ...} of app/data.json (for the "new data" banner)
"""
import glob
import http.server
import json
import os
import re
import socketserver
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
APP = os.path.join(ROOT, 'app')
ORIG = os.path.join(ROOT, 'data', 'img')
STATE = os.path.join(APP, 'state', 'user.json')
LOCK = threading.Lock()
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765


def load_state():
    try:
        with open(STATE, encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'items': {}}


def save_state(state):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(STATE), suffix='.tmp')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=APP, **kw)

    def log_message(self, fmt, *args):
        pass

    def end_headers(self):
        if self.path.split('?')[0].endswith(('.json', '.html', '.js', '.css', '/')):
            self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = self.path.split('?')[0]
        if p == '/api/state':
            with LOCK:
                return self.send_json(load_state())
        if p == '/api/version':
            f = os.path.join(APP, 'data.json')
            return self.send_json({'mtime': os.path.getmtime(f) if os.path.exists(f) else None})
        m = re.fullmatch(r'/orig/(\d+)', p)              # full-resolution sketch scan by listing id
        if m:
            hits = glob.glob(os.path.join(ORIG, f'korokiImage{m.group(1)}.*'))
            f = hits[0] if hits else None
            if f:
                with open(f, 'rb') as fh:
                    body = fh.read()
                self.send_response(200)
                self.send_header('Content-Type', 'image/png' if f.endswith('png') else 'image/jpeg')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            return self.send_error(404)
        return super().do_GET()

    def do_PUT(self):
        m = re.fullmatch(r'/api/state/(-?\d+)', self.path.split('?')[0])
        if not m:
            return self.send_error(404)
        n = int(self.headers.get('Content-Length') or 0)
        try:
            val = json.loads(self.rfile.read(n) or b'null')
        except json.JSONDecodeError:
            return self.send_json({'error': 'bad json'}, 400)
        if val is not None and not isinstance(val, dict):
            return self.send_json({'error': 'object expected'}, 400)
        with LOCK:
            state = load_state()
            if val is None:
                state['items'].pop(m.group(1), None)
            else:
                state['items'][m.group(1)] = val
            save_state(state)
        return self.send_json({'ok': True})


class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def server_bind(self):
        # skip HTTPServer's reverse-DNS lookup of the host (socket.getfqdn), which hangs behind a TUN-mode VPN
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[:2]


if __name__ == '__main__':
    srv = Server(('127.0.0.1', PORT), Handler)
    print(f'dashboard: http://127.0.0.1:{PORT}/', flush=True)
    srv.serve_forever()
