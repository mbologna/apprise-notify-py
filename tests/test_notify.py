import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from apprise_notify import notify


@pytest.fixture
def server():
    received = []
    status = {"code": 200}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers["Content-Length"])
            received.append((self.headers["Content-Type"], json.loads(self.rfile.read(length))))
            self.send_response(status["code"])
            self.end_headers()

        def log_message(self, *args):
            pass

    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}/notify/test", received, status
    httpd.shutdown()


def test_posts_json_payload(server):
    url, received, _ = server
    assert notify(url, "Title", "Body", "warning") is True
    assert received == [("application/json", {"title": "Title", "body": "Body", "type": "warning"})]


def test_default_type_is_info(server):
    url, received, _ = server
    notify(url, "t", "b")
    assert received[0][1]["type"] == "info"


def test_format_is_sent_only_when_given(server):
    url, received, _ = server
    notify(url, "t", "[a](https://x)", format_="markdown")
    notify(url, "t", "b")
    assert received[0][1]["format"] == "markdown"
    assert "format" not in received[1][1]


def test_empty_url_disables(server):
    _, received, _ = server
    assert notify("", "t", "b") is False
    assert received == []


def test_http_error_returns_false(server, capsys):
    url, _, status = server
    status["code"] = 500
    assert notify(url, "t", "b") is False
    assert "notify failed for 't'" in capsys.readouterr().err


def test_unreachable_returns_false(capsys):
    assert notify("http://127.0.0.1:9/notify/x", "t", "b", timeout=2) is False
    assert "notify failed" in capsys.readouterr().err
