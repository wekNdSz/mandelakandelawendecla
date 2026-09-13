import json
import random
import string
import os
from http.server import BaseHTTPRequestHandler

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
BOT_SECRET = os.environ.get("BOT_SECRET")
ENC_KEY = os.environ.get("ENC_KEY")

def generate_key():
    parts = [''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(4)]
    return '-'.join(parts)

def supabase_request(method, path, data=None):
    import urllib.request
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    body = json.dumps(data).encode() if data else None
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as r:
        body = r.read()
        return r.status, json.loads(body) if body else {}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        path = self.path.rstrip("/")

        if path == "/api/generate":
            if body.get("secret") != BOT_SECRET:
                return self._respond(403, {"error": "forbidden"})
            key = generate_key()
            telegram_id = body.get("telegram_id", "unknown")
            try:
                supabase_request("POST", "key", {
                    "key": key,
                    "telegram_id": str(telegram_id),
                    "active": True
                })
                self._respond(200, {"key": key})
            except Exception as e:
                self._respond(500, {"error": str(e)})

        elif path == "/api/check":
            key = body.get("key")
            hwid = body.get("hwid")
            if not key or not hwid:
                return self._respond(400, {"error": "missing key or hwid"})
            try:
                status, data = supabase_request("GET", f"key?key=eq.{key}&select=*")
                if not data:
                    return self._respond(403, {"error": "invalid key"})
                record = data[0]
                if not record.get("active"):
                    return self._respond(403, {"error": "key disabled"})
                existing_hwid = record.get("hwid")
                if existing_hwid is None:
                    supabase_request("PATCH", f"key?key=eq.{key}", {"hwid": hwid})
                    self._respond(200, {"status": "ok", "k": ENC_KEY, "telegram_id": record.get("telegram_id")})
                elif existing_hwid == hwid:
                    self._respond(200, {"status": "ok", "k": ENC_KEY, "telegram_id": record.get("telegram_id")})
                else:
                    self._respond(403, {"error": "hwid mismatch"})
            except Exception as e:
                self._respond(500, {"error": str(e)})
        else:
            self._respond(404, {"error": "not found"})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        pass
