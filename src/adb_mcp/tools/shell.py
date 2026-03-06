from adb_mcp.adb import adb_exec


def shell(command: str) -> str:
    return adb_exec("shell", command, timeout=30)
