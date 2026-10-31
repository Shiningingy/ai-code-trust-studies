"""Local logger: saves the request BODY only. Auth headers are never read or stored. Nothing is forwarded."""
import http.server, json, sys, threading
out = sys.argv[1]; seen = []
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get('content-length', 0)); b = self.rfile.read(n)
        if '/messages' in self.path and 'count_tokens' not in self.path:
            seen.append(b); open(out, 'wb').write(b)
        self.send_response(400); self.send_header('content-type', 'application/json'); self.end_headers()
        self.wfile.write(b'{"type":"error","error":{"type":"invalid_request_error","message":"logged"}}')
    def log_message(self, *a): pass
s = http.server.ThreadingHTTPServer(('127.0.0.1', int(sys.argv[2])), H)
threading.Timer(float(sys.argv[3]), s.shutdown).start(); s.serve_forever()
