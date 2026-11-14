import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

import apprise_notify
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
    thread = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
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


def test_key_without_configuration_returns_false(server, capsys):
    url, _, status = server
    status["code"] = 204
    assert notify(url, "t", "b") is False
    assert "no Apprise configuration" in capsys.readouterr().err


def test_unreachable_returns_false(capsys):
    assert notify("http://127.0.0.1:9/notify/x", "t", "b", timeout=2) is False
    assert "notify failed" in capsys.readouterr().err


# --- URL lists and failover ------------------------------------------------


@pytest.fixture
def servers():
    """Two independent servers, each recording the paths it was asked for."""
    made = []

    def make():
        hits = []
        status = {"codes": [200]}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers["Content-Length"])
                self.rfile.read(length)
                hits.append(self.path)
                codes = status["codes"]
                self.send_response(codes.pop(0) if len(codes) > 1 else codes[0])
                self.end_headers()

            def log_message(self, *args):
                pass

        httpd = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
        made.append(httpd)
        return f"http://127.0.0.1:{httpd.server_port}/notify/k", hits, status

    yield make
    for httpd in made:
        httpd.shutdown()


@pytest.fixture(autouse=True)
def no_retry_delay(monkeypatch):
    monkeypatch.setattr(apprise_notify, "RETRY_DELAY", 0)
    monkeypatch.delenv("APPRISE_URLS", raising=False)


DOWN = "http://127.0.0.1:9/notify/x"


def test_list_first_success_wins(servers):
    (u1, h1, _), (u2, h2, _) = servers(), servers()
    assert notify([u1, u2], "t", "b") is True
    assert h1 == ["/notify/k"]
    assert h2 == []


def test_space_separated_string_is_a_list(servers):
    (u1, h1, s1), (u2, h2, _) = servers(), servers()
    s1["codes"] = [404]
    assert notify(f"  {u1}   {u2}\n", "t", "b") is True
    assert h1 == ["/notify/k"]
    assert h2 == ["/notify/k"]


def test_tuple_is_accepted_and_blank_items_skipped(servers):
    u1, h1, _ = servers()
    assert notify(("", "  ", u1), "t", "b") is True
    assert h1 == ["/notify/k"]


def test_fails_over_when_first_is_unreachable(servers, capsys):
    u2, h2, _ = servers()
    assert notify([DOWN, u2], "t", "b", timeout=2) is True
    assert h2 == ["/notify/k"]
    assert capsys.readouterr().err.count("notify failed") == 2  # DOWN tried twice


def test_5xx_is_retried_once_then_succeeds(servers):
    u1, h1, s1 = servers()
    s1["codes"] = [503, 200]
    assert notify(u1, "t", "b") is True
    assert len(h1) == 2


def test_5xx_twice_moves_to_next(servers):
    (u1, h1, s1), (u2, h2, _) = servers(), servers()
    s1["codes"] = [500]
    assert notify([u1, u2], "t", "b") is True
    assert len(h1) == 2
    assert len(h2) == 1


def test_4xx_is_not_retried(servers, capsys):
    (u1, h1, s1), (u2, h2, _) = servers(), servers()
    s1["codes"] = [404]
    assert notify([u1, u2], "t", "b") is True
    assert len(h1) == 1
    assert len(h2) == 1
    assert "404" in capsys.readouterr().err


def test_204_moves_to_next_without_retry(servers, capsys):
    (u1, h1, s1), (u2, h2, _) = servers(), servers()
    s1["codes"] = [204]
    assert notify([u1, u2], "t", "b") is True
    assert len(h1) == 1
    assert len(h2) == 1
    assert "no Apprise configuration" in capsys.readouterr().err


def test_all_fail_returns_false(servers, capsys):
    (u1, h1, s1), (u2, h2, s2) = servers(), servers()
    s1["codes"], s2["codes"] = [204], [502]
    assert notify([u1, DOWN, u2], "t", "b", timeout=2) is False
    assert len(h1) == 1
    assert len(h2) == 2
    assert capsys.readouterr().err.count("notify failed") == 5


def test_empty_list_disables():
    assert notify([], "t", "b") is False
    assert notify("   ", "t", "b") is False


def test_malformed_url_is_skipped(servers, capsys):
    u1, h1, _ = servers()
    assert notify(["not-a-url", u1], "t", "b") is True
    assert h1 == ["/notify/k"]
    assert "notify failed" in capsys.readouterr().err


def test_unsupported_type_returns_false(capsys):
    assert notify(42, "t", "b") is False
    assert notify([1, 2], "t", "b") is False
    assert "unsupported apprise_url" in capsys.readouterr().err


def test_none_reads_apprise_urls_env(servers, monkeypatch):
    (u1, h1, s1), (u2, h2, _) = servers(), servers()
    s1["codes"] = [404]
    monkeypatch.setenv("APPRISE_URLS", f"{u1} {u2}")
    assert notify(None, "t", "b") is True
    assert len(h1) == 1
    assert len(h2) == 1


def test_none_without_env_disables():
    assert notify(None, "t", "b") is False


def test_empty_string_does_not_read_env(servers, monkeypatch):
    u1, h1, _ = servers()
    monkeypatch.setenv("APPRISE_URLS", u1)
    assert notify("", "t", "b") is False
    assert h1 == []
