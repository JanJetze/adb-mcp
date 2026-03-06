from adb_mcp.adb import adb_exec


def read_logs(filter: str | None = None, lines: int = 50) -> str:
    output = adb_exec("logcat", "-d", "-t", str(lines), timeout=15)
    if filter:
        filtered = [line for line in output.splitlines() if filter.lower() in line.lower()]
        return "\n".join(filtered)
    return output
