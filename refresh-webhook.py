#!/usr/bin/env python3
import subprocess, json, os
from http.server import HTTPServer, BaseHTTPRequestHandler

SCRIPT = "/root/sna-dashboard/refresh-and-deploy.sh"
PORT = 20129
KEY = os.environ.get("WEBHOOK_KEY", "sna-refresh-2026")

class H(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","POST,GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type,Authorization")
        self.end_headers()
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(json.dumps({"status":"ready"}).encode())
    def do_POST(self):
        auth=self.headers.get("Authorization","")
        if auth!="Bearer "+KEY:
            self.send_response(401)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps({"error":"Unauthorized"}).encode())
            return
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        try:
            proc=subprocess.Popen(["bash",SCRIPT],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            self.wfile.write(json.dumps({"ok":True,"pid":proc.pid,"message":"Refresh started. Update in ~2 min."}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"error":str(e)}).encode())
    def log_message(self,*a): pass

if __name__=="__main__":
    server=HTTPServer(("0.0.0.0",PORT),H)
    print(f"Webhook on port {PORT}")
    server.serve_forever()
