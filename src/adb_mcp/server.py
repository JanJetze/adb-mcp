from mcp.server.fastmcp import FastMCP

from adb_mcp.tools import device, screen, input as input_tools, app, logs, shell as shell_tools

mcp = FastMCP(
    "adb",
    instructions="""\
You control an Android device via adb over WiFi.

## Connection workflow (must be done first)
1. **First-time pairing:** The user opens Settings > Developer options > Wireless \
debugging > "Pair device with pairing code" on their phone, then gives you the \
6-digit code. Call `device_pair(code="123456")`. The device is discovered \
automatically via mDNS — you do NOT need host/port.
2. **Connect:** Call `device_connect()` each session. Auto-discovers paired devices \
on the network. No arguments needed.
3. **Verify:** Call `device_status()` to confirm the device is online.

## Interacting with the screen
- Call `screenshot()` to see what's on screen. Returns an image.
- Call `ui_tree()` to get a structured JSON of all UI elements with their text, \
resource-id, bounds, and center coordinates (cx, cy). Use these coordinates for \
tapping.
- Always call `ui_tree()` or `screenshot()` before tapping so you know the \
correct coordinates.
- After performing an action (tap, swipe, text input), take a new screenshot or \
ui_tree to verify the result.

## Input actions
- `tap(x, y)` — tap a point. Get coordinates from ui_tree bounds (cx, cy).
- `swipe(x1, y1, x2, y2)` — swipe between two points. Useful for scrolling \
(e.g., swipe from bottom to top to scroll down).
- `input_text(text)` — type into the currently focused text field. Tap a field \
first to focus it.
- `press_key(key)` — press back, home, enter, recent, delete, tab, volume_up, \
volume_down, power, or menu.

## Other tools
- `launch_app(package)` — launch an app (e.g., "com.android.settings").
- `read_logs(filter, lines)` — read logcat output, optionally filtered.
- `shell(command)` — run any adb shell command as an escape hatch.

## Tips
- If device_connect() finds nothing, ask the user to check that wireless \
debugging is enabled and the phone is on the same WiFi network.
- Screenshots are downscaled to 540px wide by default to save tokens. Use \
max_width to adjust if needed.
- ui_tree with simplified=True (default) prunes empty containers. Use \
simplified=False if you need the full hierarchy.
""",
)


@mcp.tool()
def device_pair(code: str, host: str | None = None, port: int | None = None) -> str:
    """Pair with a device for wireless debugging (one-time, Android 11+).
    Only the pairing code is required — the device is found automatically
    via network discovery. Provide host/port only as a manual override."""
    return device.device_pair(code, host, port)


@mcp.tool()
def device_connect(host: str | None = None, port: int | None = None) -> str:
    """Connect to a device over WiFi debugging. Automatically discovers
    devices on the network. Provide host/port only as a manual override."""
    return device.device_connect(host, port)


@mcp.tool()
def device_status() -> str:
    """Check connected devices and connection health."""
    return device.device_status()


@mcp.tool()
def screenshot(max_width: int = 540) -> list:
    """Capture the current screen. Returns the screenshot as an image.
    max_width controls downscaling to reduce token cost (default 540px)."""
    from mcp.types import ImageContent
    b64, mime = screen.screenshot(max_width)
    return [ImageContent(type="image", data=b64, mimeType=mime)]


@mcp.tool()
def ui_tree(simplified: bool = True) -> str:
    """Dump the UI hierarchy for element discovery. Returns a simplified JSON
    tree with text, id, bounds (including center point for tapping), and
    interaction hints. Set simplified=False for the full tree."""
    return screen.ui_tree(simplified)


@mcp.tool()
def tap(x: int, y: int) -> str:
    """Tap a screen coordinate."""
    return input_tools.tap(x, y) or "OK"


@mcp.tool()
def swipe(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> str:
    """Swipe between two points on screen."""
    return input_tools.swipe(x1, y1, x2, y2, duration_ms) or "OK"


@mcp.tool()
def input_text(text: str) -> str:
    """Type text into the currently focused field."""
    return input_tools.input_text(text) or "OK"


@mcp.tool()
def press_key(key: str) -> str:
    """Press a key. Accepts: back, home, enter, recent, delete, tab,
    volume_up, volume_down, power, menu, or a numeric keycode."""
    return input_tools.press_key(key) or "OK"


@mcp.tool()
def launch_app(package: str) -> str:
    """Launch an app by package name (e.g. com.android.settings)."""
    return app.launch_app(package)


@mcp.tool()
def read_logs(filter: str | None = None, lines: int = 50) -> str:
    """Read logcat output. Optionally filter by a string (case-insensitive)."""
    return logs.read_logs(filter, lines)


@mcp.tool()
def shell(command: str) -> str:
    """Run an arbitrary adb shell command. Use as an escape hatch when
    no specific tool covers your need."""
    return shell_tools.shell(command)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
