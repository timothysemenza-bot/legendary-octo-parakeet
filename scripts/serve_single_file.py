from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import mimetypes
import sys


class Handler(BaseHTTPRequestHandler):
    file_path = None

    def _send_headers(self, status=200):
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self):
        self._send_headers(204)
        self.end_headers()

    def do_GET(self):
        if self.path not in ("/", "/file"):
            self._send_headers(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return

        data = self.file_path.read_bytes()
        mime, _ = mimetypes.guess_type(str(self.file_path))
        self._send_headers(200)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header(
            "Content-Disposition",
            f'attachment; filename="{self.file_path.name}"',
        )
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: serve_single_file.py <port> <file_path>")

    port = int(sys.argv[1])
    Handler.file_path = Path(sys.argv[2])
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"Serving {Handler.file_path} on http://127.0.0.1:{port}/file")
    server.serve_forever()


if __name__ == "__main__":
    main()
