from adb_mcp.adb import adb_exec


def launch_app(package: str) -> str:
    return adb_exec("shell", "monkey", "-p", package,
                     "-c", "android.intent.category.LAUNCHER", "1")
