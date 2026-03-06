from adb_mcp.adb import adb_exec

KEY_MAP = {
    "back": 4, "home": 3, "recent": 187,
    "enter": 66, "delete": 67, "tab": 61,
    "volume_up": 24, "volume_down": 25,
    "power": 26, "menu": 82,
}


def _escape_text(text: str) -> str:
    result = []
    for ch in text:
        if ch == " ":
            result.append("%s")
        elif ch in r"&|;<>()$`\"'{}[]!?#*~":
            result.append(f"\\{ch}")
        else:
            result.append(ch)
    return "".join(result)


def tap(x: int, y: int) -> str:
    return adb_exec("shell", "input", "tap", str(x), str(y))


def swipe(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> str:
    return adb_exec("shell", "input", "swipe",
                     str(x1), str(y1), str(x2), str(y2), str(duration_ms))


def input_text(text: str) -> str:
    escaped = _escape_text(text)
    return adb_exec("shell", "input", "text", escaped)


def press_key(key: str) -> str:
    if key.isdigit():
        keycode = int(key)
    else:
        keycode = KEY_MAP.get(key.lower())
        if keycode is None:
            return f"Unknown key: {key}. Available: {', '.join(KEY_MAP.keys())}"
    return adb_exec("shell", "input", "keyevent", str(keycode))
