import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.request
import urllib.error

PREVIEW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui-preview")
if not os.path.exists(PREVIEW_DIR):
    print("Error: ui-preview directory not found!")
    sys.exit(1)

os.chdir(PREVIEW_DIR)

BACKEND_URL = "http://127.0.0.1:8000"
MAX_PAYLOAD_SIZE = 25 * 1024 * 1024  # 25 MB

class ProxyRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # OWASP Security Headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'SAMEORIGIN')
        self.send_header('X-XSS-Protection', '1; mode=block')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        super().end_headers()

    def list_directory(self, path):
        """Security: Disable directory listing to prevent information disclosure."""
        self.send_error(403, "Directory listing forbidden")
        return None

    def validate_path(self):
        """Security: Block path traversal attacks (e.g. ../ or %2e%2e)."""
        clean_path = self.path.split('?')[0]
        if ".." in clean_path or "%2e" in clean_path.lower() or "//" in clean_path or "\\" in clean_path:
            self.send_error(400, "Bad Request: Path traversal prohibited")
            return False
        return True

    def do_GET(self):
        if not self.validate_path():
            return
        if self.path.startswith(('/api/', '/uploads/', '/sample_scans/')):
            self.proxy_request('GET')
        else:
            super().do_GET()

    def do_POST(self):
        if not self.validate_path():
            return
        if self.path.startswith(('/api/', '/uploads/')):
            self.proxy_request('POST')
        else:
            super().do_POST()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def proxy_request(self, method):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > MAX_PAYLOAD_SIZE:
            self.send_error(413, "Payload Too Large: Max size is 25MB")
            return

        target_url = BACKEND_URL + self.path
        headers = {k: v for k, v in self.headers.items() if k.lower() not in ('host', 'content-length')}
        body = None
        if method == 'POST':
            if content_length > 0:
                body = self.rfile.read(content_length)

        req = urllib.request.Request(target_url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                self.send_response(resp.status)
                for k, v in resp.getheaders():
                    if k.lower() not in ('transfer-encoding', 'content-length', 'access-control-allow-origin'):
                        self.send_header(k, v)
                resp_data = resp.read()
                self.send_header('Content-Length', str(len(resp_data)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(resp_data)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(str(e).encode())

def run():
    port = 5050
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, ProxyRequestHandler)
    print(f"LIV-SENSI UI Preview + Proxy running at: http://0.0.0.0:{port} (Local: http://127.0.0.1:{port})")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
