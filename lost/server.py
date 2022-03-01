#!/usr/bin/env python
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from time import sleep


class LoriRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>Hello!</h1>")
        self.wfile.write(bytes("<p>This is a test server for the LoST application.<br>", "utf8"))
        self.wfile.write(bytes("It replies to POST requests that LoST normally directs to a live Lori server.</p>", "utf8"))
        self.wfile.write(bytes(f"<p>This was a GET request to {self.path}</p>", "utf8"))
        # print("do_GET()")

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b'Hello, world!<br>')
        self.wfile.write(bytes(f"This was a POST request, path was {self.path}", "utf8"))
        # print("do_POST()")


def start_testserver(port=8000):
    httpd = HTTPServer(('localhost', port), LoriRequestHandler)

    thread = threading.Thread(target=httpd.serve_forever)
    thread.start()

    return httpd


if __name__ == '__main__':
    httpd = start_testserver()
    print('Server started.')

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        pass

    httpd.shutdown()
    httpd.server_close()
    print("\nServer stopped.")
