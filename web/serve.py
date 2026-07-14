"""Tiny static server for the web version of Snake Game.

The web version is plain HTML5 + JavaScript (no build step, no wasm), so any
static server works. This one just makes local + phone testing easy.

Usage:
    python serve.py
Then open the printed URL in any browser. For your phone, use the LAN URL
(same Wi-Fi) shown below.
"""
import http.server
import socketserver
import os

PORT = 8000
os.chdir(os.path.dirname(os.path.abspath(__file__)))


class Server(socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    for port in range(PORT, PORT + 10):
        try:
            with Server(("0.0.0.0", port), http.server.SimpleHTTPRequestHandler) as httpd:
                print("Snake Game (web) is running.")
                print(f"  On this computer:  http://localhost:{port}/")
                print(f"  On your phone:     http://<this-PC-IP>:{port}/  (same Wi-Fi)")
                print("Press Ctrl+C to stop.")
                httpd.serve_forever()
            break
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except OSError:
            print(f"Port {port} busy, trying {port + 1} ...")
