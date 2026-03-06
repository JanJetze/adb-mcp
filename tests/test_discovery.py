from unittest.mock import patch, MagicMock
import subprocess

from adb_mcp.discovery import _browse, _resolve, _resolve_host, discover_services


BROWSE_OUTPUT = """\
Browsing for _adb-tls-connect._tcp.local.
DATE: ---Fri 06 Mar 2026---
17:41:38.588  ...STARTING...
17:41:38.589  Add        2  14 local.               _adb-tls-connect._tcp. adb-DEVICE1-abc123
17:41:38.590  Add        2  14 local.               _adb-tls-connect._tcp. adb-DEVICE2-def456
"""

RESOLVE_OUTPUT = """\
Lookup adb-DEVICE1-abc123._adb-tls-connect._tcp.local.
DATE: ---Fri 06 Mar 2026---
17:43:35.280  ...STARTING...
17:43:36.815  adb-DEVICE1-abc123._adb-tls-connect._tcp.local. can be reached at Android.local.:40845 (interface 14)
 api= name=SM-A528B v=1
"""

HOST_RESOLVE_OUTPUT = """\
DATE: ---Fri 06 Mar 2026---
17:43:37.000  ...STARTING...
17:43:37.100  Add  40000002  14  Android.local.  192.168.2.12  120
"""


def _make_popen(stdout_text):
    proc = MagicMock()
    proc.communicate.side_effect = subprocess.TimeoutExpired(cmd="dns-sd", timeout=3)
    proc.kill.return_value = None
    # After kill, communicate returns the buffered output
    def post_kill_communicate():
        proc.communicate.side_effect = None
        proc.communicate.return_value = (stdout_text.encode(), b"")
    proc.kill.side_effect = post_kill_communicate
    return proc


class TestBrowse:
    def test_parses_instances(self):
        proc = _make_popen(BROWSE_OUTPUT)
        with patch("adb_mcp.discovery.subprocess.Popen", return_value=proc):
            result = _browse("_adb-tls-connect._tcp.", 3.0)
            assert result == ["adb-DEVICE1-abc123", "adb-DEVICE2-def456"]

    def test_empty_output(self):
        proc = _make_popen("Browsing for ...\n...STARTING...\n")
        with patch("adb_mcp.discovery.subprocess.Popen", return_value=proc):
            result = _browse("_adb-tls-connect._tcp.", 3.0)
            assert result == []


class TestResolve:
    def test_parses_host_and_port(self):
        resolve_proc = _make_popen(RESOLVE_OUTPUT)
        host_proc = _make_popen(HOST_RESOLVE_OUTPUT)
        procs = iter([resolve_proc, host_proc])
        with patch("adb_mcp.discovery.subprocess.Popen", side_effect=lambda *a, **kw: next(procs)):
            result = _resolve("adb-DEVICE1-abc123", "_adb-tls-connect._tcp.", 3.0)
            assert result == {
                "name": "adb-DEVICE1-abc123",
                "host": "192.168.2.12",
                "port": 40845,
            }

    def test_returns_none_on_empty(self):
        proc = _make_popen("Lookup ...\n...STARTING...\n")
        with patch("adb_mcp.discovery.subprocess.Popen", return_value=proc):
            result = _resolve("missing", "_adb-tls-connect._tcp.", 3.0)
            assert result is None


class TestResolveHost:
    def test_parses_ip(self):
        proc = _make_popen(HOST_RESOLVE_OUTPUT)
        with patch("adb_mcp.discovery.subprocess.Popen", return_value=proc):
            assert _resolve_host("Android.local.", 3.0) == "192.168.2.12"

    def test_returns_none_on_no_match(self):
        proc = _make_popen("...STARTING...\n")
        with patch("adb_mcp.discovery.subprocess.Popen", return_value=proc):
            assert _resolve_host("missing.local.", 3.0) is None


class TestDiscoverServices:
    @patch("adb_mcp.discovery._DNS_SD", None)
    def test_returns_empty_without_dns_sd(self):
        result = discover_services("_adb-tls-connect._tcp.")
        assert result == []
