# adb-mcp

MCP server that lets Claude interact with Android devices — take screenshots, tap buttons, read UI elements, type text, and more.

## How it works

```
Claude Code  <-->  MCP Server (Python, on host)
                       |
                       v  (adb over WiFi / TCP)
               Android Device
```

The MCP server runs on your machine and calls adb directly. Claude can see your phone's screen, read the UI hierarchy to find elements, and interact with them by tapping, swiping, and typing. Devices are discovered automatically on the network via mDNS.

## Prerequisites

- **adb** — `brew install android-platform-tools` (macOS) or `apt install adb` (Linux)
- **[uv](https://docs.astral.sh/uv/)** (Python package manager)
- **Android device** with wireless debugging enabled (Android 11+)

## Setup

### 1. Enable wireless debugging on your Android device

1. Go to **Settings > Developer options** (enable developer options first if needed by tapping Build Number 7 times in **Settings > About phone**)
2. Enable **Wireless debugging**
3. Keep this screen open — you'll need it for pairing

### 2. Add the MCP server to Claude Code

Add to your Claude Code settings (`~/.claude/settings.json` under `mcpServers`), or use the `/mcp` dialog:

```json
{
  "adb-mcp": {
    "command": "uv",
    "args": ["run", "--directory", "/path/to/adb-mcp", "adb-mcp"],
    "type": "stdio"
  }
}
```

### 3. Pair and connect your device

**On macOS**, devices are discovered automatically via mDNS — no need to type IP addresses or ports:

1. On your phone, tap **Pair device with pairing code** in the wireless debugging screen
2. Tell Claude the 6-digit code: *"Pair my phone, code 123456"*
3. Then: *"Connect to my phone"*

**On Linux**, provide the IP and port shown on the wireless debugging screen:

1. *"Pair my phone at 192.168.1.100 port 37123, code 123456"*
2. *"Connect to my phone at 192.168.1.100 port 40845"*

## Tools

| Tool | Description |
|------|-------------|
| `device_pair` | Pair with a device for wireless debugging (one-time) |
| `device_connect` | Connect to a device over WiFi |
| `device_status` | List connected devices |
| `screenshot` | Capture the screen (returned as image, auto-scaled) |
| `ui_tree` | Dump the UI hierarchy as structured JSON |
| `tap` | Tap a screen coordinate |
| `swipe` | Swipe between two points |
| `input_text` | Type text into the focused field |
| `press_key` | Press a key (back, home, enter, etc.) |
| `launch_app` | Launch an app by package name |
| `install_app` | Install an APK from the host machine onto the device (supports `reinstall` flag to keep data) |
| `read_logs` | Read logcat output with optional filtering |
| `shell` | Run an arbitrary adb shell command |

## Usage examples

Once connected, you can ask Claude things like:

- *"Take a screenshot of my phone"*
- *"What app is currently open?"*
- *"Open the Settings app"*
- *"Tap on the Wi-Fi option"*
- *"Scroll down on this screen"*
- *"Type 'hello world' into the search field"*
- *"Go back to the home screen"*
- *"Show me the recent logs from my app com.example.myapp"*

Claude will use `screenshot` and `ui_tree` to see the screen, identify elements and their coordinates, and then use `tap`/`swipe`/`input_text` to interact.

## Development

```bash
git clone https://github.com/janjetze/adb-mcp.git
cd adb-mcp

# Run the server
uv run adb-mcp

# Or install in a venv for development
uv venv
uv pip install -e .
```

## License

MIT
