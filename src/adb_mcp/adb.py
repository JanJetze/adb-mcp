import shutil
import subprocess


def _find_adb() -> str:
    path = shutil.which("adb")
    if path:
        return path
    raise FileNotFoundError(
        "adb not found on PATH. Install it with:\n"
        "  brew install android-platform-tools"
    )


ADB = _find_adb()


def adb_exec(*args: str, timeout: float = 10) -> str:
    result = subprocess.run(
        [ADB] + list(args),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0 and result.stderr:
        return result.stderr.strip()
    return result.stdout.strip()


def adb_exec_binary(*args: str, timeout: float = 10) -> bytes:
    result = subprocess.run(
        [ADB] + list(args),
        capture_output=True,
        timeout=timeout,
    )
    if result.returncode != 0 and result.stderr:
        raise RuntimeError(result.stderr.decode(errors="replace").strip())
    return result.stdout
