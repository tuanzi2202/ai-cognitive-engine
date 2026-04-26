import http.client
import os
import ssl
import sys
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


PROXY_PREFIX = "/api/v1"
UPSTREAM_BASE = os.environ.get("ZENMUX_UPSTREAM_BASE", "https://zenmux.ai").rstrip("/")


def _parse_upstream_base(base: str):
    parsed = urllib.parse.urlsplit(base)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("ZENMUX_UPSTREAM_BASE must be an https URL with a hostname")
    prefix = parsed.path.rstrip("/")
    return parsed.hostname, parsed.port or 443, prefix


UPSTREAM_HOST, UPSTREAM_PORT, UPSTREAM_PREFIX = _parse_upstream_base(UPSTREAM_BASE)
UPSTREAM_SSL_CONTEXT = ssl.create_default_context()


class Handler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def end_headers(self):
        # Keep it simple: allow the static app to call this local proxy from any origin (file:// included).
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, Accept, X-Requested-With")
        self.send_header("Access-Control-Expose-Headers", "X-ZenMux-RequestId")
        self.send_header("Access-Control-Max-Age", "86400")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        if self._is_proxy_request():
            return self._proxy()
        return super().do_GET()

    def do_POST(self):
        if self._is_proxy_request():
            return self._proxy()
        self.send_error(404, "Not Found")

    def do_PUT(self):
        if self._is_proxy_request():
            return self._proxy()
        self.send_error(404, "Not Found")

    def do_PATCH(self):
        if self._is_proxy_request():
            return self._proxy()
        self.send_error(404, "Not Found")

    def do_DELETE(self):
        if self._is_proxy_request():
            return self._proxy()
        self.send_error(404, "Not Found")

    def _is_proxy_request(self) -> bool:
        return self.path == PROXY_PREFIX or self.path.startswith(PROXY_PREFIX + "/")

    def _proxy(self):
        parsed = urllib.parse.urlsplit(self.path)
        upstream_path = (UPSTREAM_PREFIX + parsed.path) if UPSTREAM_PREFIX else parsed.path
        if parsed.query:
            upstream_path += "?" + parsed.query

        content_length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(content_length) if content_length > 0 else None

        # Forward most headers; drop hop-by-hop and encoding headers.
        forward_headers = {}
        for key, value in self.headers.items():
            k = key.lower()
            if k in ("host", "connection", "content-length"):
                continue
            if k == "accept-encoding":
                continue
            forward_headers[key] = value
        forward_headers["Host"] = UPSTREAM_HOST

        conn = http.client.HTTPSConnection(
            UPSTREAM_HOST,
            UPSTREAM_PORT,
            context=UPSTREAM_SSL_CONTEXT,
            timeout=300,
        )
        try:
            conn.request(self.command, upstream_path, body=body, headers=forward_headers)
            res = conn.getresponse()

            self.send_response(res.status, res.reason)

            # Copy response headers except hop-by-hop and CORS (we set our own).
            for key, value in res.headers.items():
                k = key.lower()
                if k in (
                    "connection",
                    "keep-alive",
                    "proxy-authenticate",
                    "proxy-authorization",
                    "te",
                    "trailers",
                    "transfer-encoding",
                    "upgrade",
                ):
                    continue
                if k.startswith("access-control-"):
                    continue
                # BaseHTTPRequestHandler will manage Content-Length/close semantics for us.
                self.send_header(key, value)
            self.end_headers()

            # Stream through (supports SSE).
            while True:
                chunk = res.read(8192)
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                    self.wfile.flush()
                except BrokenPipeError:
                    break
        finally:
            try:
                conn.close()
            except Exception:
                pass


def main():
    port = 8787
    if len(sys.argv) >= 2:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Usage: python zenmux_proxy_server.py [port]", file=sys.stderr)
            return 2

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Serving on http://127.0.0.1:{port}")
    print(f"Proxying {PROXY_PREFIX}/* -> {UPSTREAM_BASE}{PROXY_PREFIX}/*")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

