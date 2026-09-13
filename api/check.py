import json
import os
from http.server import BaseHTTPRequestHandler

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

def get_key(key):
    import urllib.request
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/key?key=eq.{key}&select=*",
        headers={
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        }
    )
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
        return data[0] if data else None

def update_hwid(key, hwid):
    import urllib.request
    data = json.dumps({"hwid": hwid}).encode()
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/key?key=eq.{key}",
        data=data,
        headers={
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        },
        method="PATCH"
    )
    with urllib.request.urlopen(req) as r:
        return r.status == 204

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        
        key = body.get("key")
        hwid = body.get("hwid")
        
        if not key or not hwid:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error":"missing key or hwid"}')
            return
        
        try:
            record = get_key(key)
            
            if not record:
                self._respond(403, {"error": "invalid key"})
                return
            
            if not record.get("active"):
                self._respond(403, {"error": "key disabled"})
                return
            
            existing_hwid = record.get("hwid")
            
            if existing_hwid is None:
                # первый запуск — привязываем hwid
                update_hwid(key, hwid)
                self._respond(200, {"status": "ok", "message": "activated"})
            elif existing_hwid == hwid:
                # тот же девайс
                self._respond(200, {"status": "ok"})
            else:
                # чужой девайс
                self._respond(403, {"error": "hwid mismatch"})
                
        except Exception as e:
            self._respond(500, {"error": str(e)})
    
    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        pass
