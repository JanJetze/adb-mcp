from unittest.mock import patch

from adb_mcp.tools.input import _escape_text, press_key
from adb_mcp.tools.app import launch_app
from adb_mcp.tools.logs import read_logs


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
