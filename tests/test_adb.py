from unittest.mock import patch, MagicMock
import subprocess

from adb_mcp.adb import adb_exec, adb_exec_binary


@patch("adb_mcp.adb.ADB", "/usr/bin/adb")
class TestAdbExec:
    def test_returns_stdout_on_success(self):
        result = MagicMock(returncode=0, stdout="List of devices attached\n", stderr="")
        with patch("adb_mcp.adb.subprocess.run", return_value=result) as mock_run:
            output = adb_exec("devices")
            assert output == "List of devices attached"
            mock_run.assert_called_once_with(
                ["/usr/bin/adb", "devices"],
                capture_output=True, text=True, timeout=10,
            )

    def test_returns_stderr_on_failure(self):
        result = MagicMock(returncode=1, stdout="", stderr="error: no devices\n")
        with patch("adb_mcp.adb.subprocess.run", return_value=result):
            output = adb_exec("devices")
            assert output == "error: no devices"

    def test_custom_timeout(self):
        result = MagicMock(returncode=0, stdout="ok", stderr="")
        with patch("adb_mcp.adb.subprocess.run", return_value=result) as mock_run:
            adb_exec("shell", "ls", timeout=30)
            assert mock_run.call_args[1]["timeout"] == 30

    def test_timeout_raises(self):
        with patch("adb_mcp.adb.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="adb", timeout=10)):
            try:
                adb_exec("devices")
                assert False, "Should have raised"
            except subprocess.TimeoutExpired:
                pass


@patch("adb_mcp.adb.ADB", "/usr/bin/adb")
class TestAdbExecBinary:
    def test_returns_bytes_on_success(self):
        result = MagicMock(returncode=0, stdout=b"\x89PNG", stderr=b"")
        with patch("adb_mcp.adb.subprocess.run", return_value=result):
            output = adb_exec_binary("exec-out", "screencap", "-p")
            assert output == b"\x89PNG"

    def test_raises_on_failure(self):
        result = MagicMock(returncode=1, stdout=b"", stderr=b"device not found")
        with patch("adb_mcp.adb.subprocess.run", return_value=result):
            try:
                adb_exec_binary("exec-out", "screencap", "-p")
                assert False, "Should have raised"
            except RuntimeError as e:
                assert "device not found" in str(e)
