#!/usr/bin/env python
import json, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from time import sleep
from urllib.parse import parse_qs


class LoriRequestHandler(BaseHTTPRequestHandler):

    def log_request(self, code='-', size='-'):
        # This method overrides the method in the base class in order to silence it:
        # As we're using this server mainly for the test cases, the output would just
        # interfere with the normal test output and we check for proper function in
        # the tests anyway.
        pass

    def log_error(self, *args):
        # Called by `send_error()`. Overridden with the same intention as with
        # `log_request()`.
        pass

    def send_json(self, content):
        body = json.dumps(content).encode('utf-8')
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        print(f"{self.command = },\n{self.path = },\n{self.headers.items() = }")

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>Hello!</h1>")
        self.wfile.write(bytes("<p>This is a test server for the LoST application.<br>", "utf8"))
        self.wfile.write(bytes("It replies to POST requests that LoST normally directs to a live Lori server.</p>", "utf8"))
        self.wfile.write(bytes(f"<p>This was a GET request to {self.path}</p>", "utf8"))

    def do_POST(self):
        # print(f"{self.command = },\n{self.path = },\n{self.headers.items() = }")

        if self.path == "/old/path/now/redirected/":
            # Clients can call this in order to test redirection.
            self.send_response(301)
            self.send_header('Location', f'http://{self.server.server_name}:{self.server.server_port}/redirect-goal/')
            self.end_headers()
            return

        if self.path == "/redirect-goal/":
            # A client that properly followed the above redirection gets here.
            self.send_json({'success': "The redirect went well!"})
            return

        if self.path == "/timeout/":
            # A client must properly deal with a timeout if it calls this.
            sleep(0.1)
            # The client is no longer listening. Sending something now would yield a `BrokenPipeError`.
            # self.send_json({'error': "The client should timeout before it gets this!"})
            return

        if self.path == "/non-json-reply/":
            # An improperly configured client might call a URL at which it gets a reply that is not JSON.
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b'<h1>Hello, world!</h1><p>This is HTML, not JSON.</p>')
            return

        if self.path != "/stempeluhr/event/submit/":
            # An improperly configured client might call a URL that does not exist.
            self.send_error(404)
            return

        # Technically, all is well: the client got through to the Lori server.
        l = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(l)
        rawd = parse_qs(body.decode())
        data = {key: value[0] for key, value in rawd.items()}
        # print(data)

        # self.send_json({'success': "Hello from Lori!"})
        data['echo_server_note'] = "This reply is an echo of the received data, plus this message."
        self.send_json(data)    # reply with echo
        return


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
