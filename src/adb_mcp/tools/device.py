from adb_mcp.adb import adb_exec, set_device_serial
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


def device_connect(host: str | None = None, port: int | None = None) -> str:
    if host:
        serial = f"{host}:{port or 5555}"
        result = adb_exec("connect", serial, timeout=15)
        if "connected" in result:
            set_device_serial(serial)
        return result

    devices = discover_connect_devices(timeout=5.0)
    if not devices:
        return (
            "No devices found on the network. Make sure wireless debugging "
            "is enabled on your phone and it's on the same network."
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


def device_status() -> str:
    return adb_exec("devices", "-l")
