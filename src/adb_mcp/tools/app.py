from adb_mcp.adb import adb_exec


def launch_app(package: str) -> str:
    return adb_exec("shell", "monkey", "-p", package,
                     "-c", "android.intent.category.LAUNCHER", "1")


def install_app(apk_path: str, reinstall: bool = False) -> str:
    args = ["install"]
    if reinstall:
        args.append("-r")
    args.append(apk_path)
    return adb_exec(*args, timeout=120)
