from adb_mcp.adb import adb_exec, set_device_serial, get_device_serial
from adb_mcp.discovery import discover_pairing_devices, discover_connect_devices


def device_pair(code: str, host: str | None = None, port: int | None = None) -> str:
    if host and port:
        return adb_exec("pair", f"{host}:{port}", code, timeout=15)

    devices = discover_pairing_devices(timeout=5.0)
    if not devices:
        return (
            "No pairing services found on the network. Make sure you tapped "
            "'Pair device with pairing code' on your phone and the pairing "
            "dialog is still open."
        )

    if len(devices) == 1:
        d = devices[0]
        result = adb_exec("pair", f"{d['host']}:{d['port']}", code, timeout=15)
        return f"Found {d['name']} at {d['host']}:{d['port']}\n{result}"

    lines = ["Multiple pairing services found. Pairing with all:\n"]
    for d in devices:
        result = adb_exec("pair", f"{d['host']}:{d['port']}", code, timeout=15)
        lines.append(f"  {d['name']} ({d['host']}:{d['port']}): {result}")
    return "\n".join(lines)


def _deduplicate_devices(devices: list[dict]) -> list[dict]:
    """Keep only one entry per unique IP address."""
    seen: dict[str, dict] = {}
    for d in devices:
        host = d["host"]
        if host not in seen:
            seen[host] = d
    return list(seen.values())


def _find_local_devices() -> list[dict]:
    """Check `adb devices` for already-connected devices (e.g. local emulators)."""
    output = adb_exec("devices", "-l")
    devices = []
    for line in output.splitlines():
        if "\tdevice" not in line:
            continue
        serial = line.split("\t")[0]
        model = ""
        for part in line.split():
            if part.startswith("model:"):
                model = part.split(":", 1)[1]
                break
        devices.append({"serial": serial, "model": model or serial})
    return devices


def device_connect(host: str | None = None, port: int | None = None) -> str:
    if host:
        serial = f"{host}:{port or 5555}"
        result = adb_exec("connect", serial, timeout=15)
        if "connected" in result:
            set_device_serial(serial)
        return result

    # Check for already-connected local devices (emulators, USB)
    local = _find_local_devices()
    if local:
        current = get_device_serial()
        # If we already have a selected device that's still connected and it's
        # the only device, keep it. With multiple devices, always report all.
        if current and any(d["serial"] == current for d in local) and len(local) == 1:
            return f"Already connected to {current}"

        # Keep current selection if still valid, otherwise pick the first
        if current and any(d["serial"] == current for d in local):
            chosen_serial = current
        else:
            chosen_serial = local[0]["serial"]
            set_device_serial(chosen_serial)

        if len(local) == 1:
            chosen = local[0]
            return f"Connected to {chosen['model']} ({chosen['serial']})"
        lines = [f"Found {len(local)} devices. Use set_active_device(serial) to switch:"]
        for d in local:
            marker = " (active)" if d["serial"] == chosen_serial else ""
            lines.append(f"  {d['model']} ({d['serial']}){marker}")
        return "\n".join(lines)

    # Fall back to mDNS network discovery
    devices = discover_connect_devices(timeout=5.0)
    if not devices:
        return (
            "No devices found. Make sure either:\n"
            "- A local emulator is running, or\n"
            "- Wireless debugging is enabled on your phone and it's on the same network."
        )

    devices = _deduplicate_devices(devices)

    lines = []
    connected_serial = None
    for d in devices:
        serial = f"{d['host']}:{d['port']}"
        result = adb_exec("connect", serial, timeout=15)
        if "connected" in result and connected_serial is None:
            connected_serial = serial
        lines.append(f"{d['name']} ({serial}): {result}")

    if connected_serial:
        set_device_serial(connected_serial)

    if len(lines) == 1:
        return lines[0]
    return "Found multiple devices:\n" + "\n".join(f"  {l}" for l in lines)


def list_devices() -> list[dict]:
    """Return all connected adb devices with serial and model."""
    return _find_local_devices()


def set_active_device(serial: str) -> str:
    """Set which device to target for subsequent commands."""
    devices = _find_local_devices()
    serials = [d["serial"] for d in devices]
    if serial not in serials:
        available = ", ".join(serials) if serials else "none"
        return f"Device '{serial}' not found. Available devices: {available}"
    set_device_serial(serial)
    model = next((d["model"] for d in devices if d["serial"] == serial), serial)
    return f"Active device set to {model} ({serial})"


def device_status() -> str:
    return adb_exec("devices", "-l")
