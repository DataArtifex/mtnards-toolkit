from unittest.mock import MagicMock, patch

from dartfx.mtnards.cli import RdsShell
from dartfx.mtnards.server import MtnaRdsServer


def test_api_request_debug_verbose_redacts_headers_and_prints_response(capsys):
    response = MagicMock()
    response.status_code = 200
    response.headers = {"Content-Type": "application/json", "Set-Cookie": "session=secret"}
    response.text = '{"ok": true}'
    response.json.return_value = {"ok": True}

    with patch("requests.request", return_value=response):
        server = MtnaRdsServer(host="https://example.org", api_key="secret-key", debug=True, debug_verbose=True)
        server.api_request("server/info")

    stderr = capsys.readouterr().err

    assert "RDS API:" in stderr
    assert "Request headers:" in stderr
    assert "X-API-KEY" in stderr
    assert "secret-key" in stderr
    assert "***REDACTED***" in stderr
    assert "Set-Cookie" in stderr
    assert "Response headers:" in stderr
    assert "Response body:" in stderr


def test_cli_debug_verbose_toggle():
    shell = RdsShell(host="http://test", api_key="test-key")
    shell._server = MagicMock()
    shell.server.debug_verbose = False

    should_continue = shell.execute_line("debug verbose on")

    assert should_continue is True
    assert shell.server.debug_verbose is True
