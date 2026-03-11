import os
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

_device_serial: str | None = os.environ.get("ADB_DEVICE_SERIAL")


def set_device_serial(serial: str | None) -> None:
    global _device_serial
    _device_serial = serial


def get_device_serial() -> str | None:
    return _device_serial


def _base_cmd() -> list[str]:
    if _device_serial:
        return [ADB, "-s", _device_serial]
    return [ADB]


def adb_exec(*args: str, timeout: float = 10) -> str:
    result = subprocess.run(
        _base_cmd() + list(args),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0 and result.stderr:
        return result.stderr.strip()
    return result.stdout.strip()


def adb_exec_binary(*args: str, timeout: float = 10) -> bytes:
    result = subprocess.run(
        _base_cmd() + list(args),
        capture_output=True,
        timeout=timeout,
    )
    if result.returncode != 0 and result.stderr:
        raise RuntimeError(result.stderr.decode(errors="replace").strip())
    return result.stdout
