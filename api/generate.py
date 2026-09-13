import json
import random
import string
import os
from http.server import BaseHTTPRequestHandler

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
BOT_SECRET = os.environ.get("BOT_SECRET")  
def generate_key():
    parts = []
    for _ in range(4):
        part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        parts.append(part)
    return '-'.join(parts)

def insert_key(key, telegram_id):
    import urllib.request
    data = json.dumps({
        "key": key,
        "telegram_id": str(telegram_id),
        "active": True
    }).encode()
    
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/key",
        data=data,
        headers={
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as r:
        return r.status == 201

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        
        # проверка секрета бота
        if body.get("secret") != BOT_SECRET:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b'{"error":"forbidden"}')
            return
        
        telegram_id = body.get("telegram_id", "unknown")
        key = generate_key()
        
        try:
            insert_key(key, telegram_id)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"key": key}).encode())
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def log_message(self, format, *args):
        pass
