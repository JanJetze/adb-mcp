from unittest.mock import patch

from adb_mcp.adb import set_device_serial, get_device_serial
from adb_mcp.tools.input import _escape_text, press_key
from adb_mcp.tools.app import launch_app
from adb_mcp.tools.logs import read_logs
from adb_mcp.tools.device import device_connect, _deduplicate_devices, list_devices, set_active_device
from adb_mcp.tools.app import install_app


class TestEscapeText:
    def test_spaces(self):
        assert _escape_text("hello world") == "hello%sworld"

    def test_special_chars(self):
        assert _escape_text("a&b") == "a\\&b"
        assert _escape_text("(test)") == "\\(test\\)"

    def test_plain_text(self):
        assert _escape_text("hello") == "hello"

    def test_empty(self):
        assert _escape_text("") == ""


class TestPressKey:
    @patch("adb_mcp.tools.input.adb_exec", return_value="")
    def test_named_key(self, mock_exec):
        press_key("back")
        mock_exec.assert_called_once_with("shell", "input", "keyevent", "4")

    @patch("adb_mcp.tools.input.adb_exec", return_value="")
    def test_numeric_keycode(self, mock_exec):
        press_key("66")
        mock_exec.assert_called_once_with("shell", "input", "keyevent", "66")

    def test_unknown_key(self):
        result = press_key("nonexistent")
        assert "Unknown key" in result

    @patch("adb_mcp.tools.input.adb_exec", return_value="")
    def test_case_insensitive(self, mock_exec):
        press_key("HOME")
        mock_exec.assert_called_once_with("shell", "input", "keyevent", "3")


class TestLaunchApp:
    @patch("adb_mcp.tools.app.adb_exec", return_value="Events injected: 1")
    def test_calls_monkey(self, mock_exec):
        result = launch_app("com.android.settings")
        mock_exec.assert_called_once_with(
            "shell", "monkey", "-p", "com.android.settings",
            "-c", "android.intent.category.LAUNCHER", "1",
        )
        assert "Events injected" in result


class TestReadLogs:
    @patch("adb_mcp.tools.logs.adb_exec", return_value="line1 ERROR foo\nline2 INFO bar\nline3 ERROR baz")
    def test_unfiltered(self, mock_exec):
        result = read_logs()
        assert "line1" in result
        assert "line2" in result
        assert "line3" in result

    @patch("adb_mcp.tools.logs.adb_exec", return_value="line1 ERROR foo\nline2 INFO bar\nline3 ERROR baz")
    def test_filtered(self, mock_exec):
        result = read_logs(filter="error")
        assert "line1 ERROR foo" in result
        assert "line3 ERROR baz" in result
        assert "INFO bar" not in result

    @patch("adb_mcp.tools.logs.adb_exec", return_value="line1\nline2")
    def test_custom_lines(self, mock_exec):
        read_logs(lines=100)
        args = mock_exec.call_args[0]
        assert "100" in args


class TestInstallApp:
    @patch("adb_mcp.tools.app.adb_exec", return_value="Success")
    def test_install(self, mock_exec):
        result = install_app("/tmp/app.apk")
        mock_exec.assert_called_once_with("install", "/tmp/app.apk", timeout=120)
        assert "Success" in result

    @patch("adb_mcp.tools.app.adb_exec", return_value="Success")
    def test_reinstall(self, mock_exec):
        result = install_app("/tmp/app.apk", reinstall=True)
        mock_exec.assert_called_once_with("install", "-r", "/tmp/app.apk", timeout=120)
        assert "Success" in result


class TestDeduplicateDevices:
    def test_removes_duplicate_ips(self):
        devices = [
            {"name": "device-a", "host": "192.168.1.10", "port": 40845},
            {"name": "device-b", "host": "192.168.1.10", "port": 40846},
        ]
        result = _deduplicate_devices(devices)
        assert len(result) == 1
        assert result[0]["name"] == "device-a"

    def test_keeps_different_ips(self):
        devices = [
            {"name": "phone", "host": "192.168.1.10", "port": 40845},
            {"name": "tablet", "host": "192.168.1.11", "port": 40845},
        ]
        result = _deduplicate_devices(devices)
        assert len(result) == 2

    def test_empty_list(self):
        assert _deduplicate_devices([]) == []


class TestListDevices:
    @patch("adb_mcp.tools.device.adb_exec", return_value="List of devices attached\nemulator-5554\tdevice model:sdk_phone\n192.168.1.10:5555\tdevice model:Pixel_7")
    def test_returns_all_devices(self, mock_exec):
        devices = list_devices()
        assert len(devices) == 2
        assert devices[0]["serial"] == "emulator-5554"
        assert devices[1]["serial"] == "192.168.1.10:5555"

    @patch("adb_mcp.tools.device.adb_exec", return_value="List of devices attached\nemulator-5554          device product:sdk_phone model:sdk_phone transport_id:1\n192.168.1.10:5555      device product:redfin model:Pixel_5 transport_id:2")
    def test_returns_all_devices_space_separated(self, mock_exec):
        devices = list_devices()
        assert len(devices) == 2
        assert devices[0]["serial"] == "emulator-5554"
        assert devices[0]["model"] == "sdk_phone"
        assert devices[1]["serial"] == "192.168.1.10:5555"
        assert devices[1]["model"] == "Pixel_5"

    @patch("adb_mcp.tools.device.adb_exec", return_value="List of devices attached\nemulator-5554          unauthorized transport_id:1")
    def test_skips_unauthorized_devices(self, mock_exec):
        devices = list_devices()
        assert len(devices) == 0

    @patch("adb_mcp.tools.device.adb_exec", return_value="List of devices attached\n")
    def test_returns_empty_when_no_devices(self, mock_exec):
        assert list_devices() == []


class TestSetActiveDevice:
    def setup_method(self):
        set_device_serial(None)

    @patch("adb_mcp.tools.device.adb_exec", return_value="List of devices attached\nemulator-5554\tdevice model:sdk_phone\n192.168.1.10:5555\tdevice model:Pixel_7")
    def test_sets_serial(self, mock_exec):
        result = set_active_device("emulator-5554")
        assert get_device_serial() == "emulator-5554"
        assert "sdk_phone" in result

    @patch("adb_mcp.tools.device.adb_exec", return_value="List of devices attached\nemulator-5554\tdevice model:sdk_phone")
    def test_rejects_unknown_serial(self, mock_exec):
        result = set_active_device("nonexistent-1234")
        assert get_device_serial() is None
        assert "not found" in result
        assert "emulator-5554" in result

    @patch("adb_mcp.tools.device.adb_exec", return_value="List of devices attached\n")
    def test_rejects_when_no_devices(self, mock_exec):
        result = set_active_device("emulator-5554")
        assert "not found" in result
        assert "none" in result


class TestDeviceConnect:
    def setup_method(self):
        set_device_serial(None)

    @patch("adb_mcp.tools.device.adb_exec", return_value="connected to 192.168.1.10:5555")
    def test_manual_host_sets_serial(self, mock_exec):
        device_connect(host="192.168.1.10", port=5555)
        assert get_device_serial() == "192.168.1.10:5555"

    @patch("adb_mcp.tools.device.discover_connect_devices", return_value=[
        {"name": "device-a", "host": "192.168.1.10", "port": 40845},
        {"name": "device-b", "host": "192.168.1.10", "port": 40846},
    ])
    @patch("adb_mcp.tools.device._find_local_devices", return_value=[])
    def test_auto_deduplicates_and_sets_serial(self, mock_find, mock_discover):
        with patch("adb_mcp.tools.device.adb_exec", return_value="connected to 192.168.1.10:40845") as mock_exec:
            result = device_connect()
            # Should only connect once (deduplicated)
            mock_exec.assert_called_once()
            assert get_device_serial() == "192.168.1.10:40845"

    @patch("adb_mcp.tools.device.adb_exec", return_value="failed to connect")
    def test_manual_host_no_serial_on_failure(self, mock_exec):
        device_connect(host="192.168.1.10")
        assert get_device_serial() is None

    @patch("adb_mcp.tools.device._find_local_devices", return_value=[
        {"serial": "emulator-5554", "model": "sdk_phone"},
        {"serial": "192.168.1.10:5555", "model": "Pixel_7"},
    ])
    def test_multiple_devices_reports_all(self, mock_find):
        result = device_connect()
        assert "set_active_device" in result
        assert "emulator-5554" in result
        assert "192.168.1.10:5555" in result

    @patch("adb_mcp.tools.device._find_local_devices", return_value=[
        {"serial": "emulator-5554", "model": "sdk_phone"},
        {"serial": "192.168.1.10:5555", "model": "Pixel_7"},
    ])
    def test_multiple_devices_keeps_current_selection(self, mock_find):
        set_device_serial("192.168.1.10:5555")
        result = device_connect()
        # Should keep existing selection, not reset to first
        assert get_device_serial() == "192.168.1.10:5555"
        assert "(active)" in result
