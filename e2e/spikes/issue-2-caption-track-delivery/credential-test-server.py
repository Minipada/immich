import http.server
import socketserver

VTT = b"WEBVTT\n\n00:00:00.000 --> 00:00:04.000\nprotected cue\n"
SESSION_COOKIE_VALUE = "test-session-abc123"


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/login":
            self.send_response(200)
            self.send_header("Set-Cookie", f"immich_session={SESSION_COOKIE_VALUE}; Path=/; HttpOnly; SameSite=Lax")
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>logged in</body></html>")
            return

        if self.path == "/page":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"""<html><body>
                <video id=v controls>
                  <track kind="subtitles" src="/protected.vtt" srclang="en" label="English" default>
                </video>
                <script>window.__loaded = true;</script>
                </body></html>"""
            )
            return

        if self.path == "/protected.vtt":
            cookie_header = self.headers.get("Cookie", "")
            if f"immich_session={SESSION_COOKIE_VALUE}" in cookie_header:
                self.send_response(200)
                self.send_header("Content-Type", "text/vtt")
                self.end_headers()
                self.wfile.write(VTT)
            else:
                self.send_response(401)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"unauthorized: no valid session cookie")
            return

        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    with socketserver.TCPServer(("127.0.0.1", 8956), Handler) as httpd:
        httpd.serve_forever()
