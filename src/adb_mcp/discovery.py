import platform
import re
import shutil
import subprocess

PAIRING_SERVICE = "_adb-tls-pairing._tcp."
CONNECT_SERVICE = "_adb-tls-connect._tcp."

_DNS_SD = shutil.which("dns-sd")


def _browse(service_type: str, timeout: float = 3.0) -> list[str]:
    """Use dns-sd to browse for service instances. Returns instance names."""
    try:
        proc = subprocess.Popen(
            ["dns-sd", "-B", service_type, "local."],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        stdout, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, _ = proc.communicate()

    instances = []
    for line in stdout.decode(errors="replace").splitlines():
        # Lines look like: "17:41:38.589  Add  2  14 local.  _adb-tls-connect._tcp.  instance-name"
        parts = line.split()
        if len(parts) >= 7 and parts[1] == "Add":
            instances.append(parts[6])
    return instances


def _resolve(instance: str, service_type: str, timeout: float = 3.0) -> dict | None:
    """Use dns-sd to resolve an instance to host:port."""
    try:
        proc = subprocess.Popen(
            ["dns-sd", "-L", instance, service_type, "local."],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        stdout, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, _ = proc.communicate()

    host = None
    port = None
    for line in stdout.decode(errors="replace").splitlines():
        # Line: "instance._adb-tls-connect._tcp.local. can be reached at hostname.local.:port"
        m = re.search(r'can be reached at\s+(\S+):(\d+)', line)
        if m:
            host = m.group(1)
            port = int(m.group(2))
            break

    if not host or not port:
        return None

    # Resolve hostname to IP
    ip = _resolve_host(host, timeout)
    return {"name": instance, "host": ip or host, "port": port}


def _resolve_host(hostname: str, timeout: float = 3.0) -> str | None:
    """Resolve a .local hostname to an IP address."""
    try:
        proc = subprocess.Popen(
            ["dns-sd", "-G", "v4", hostname],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        stdout, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, _ = proc.communicate()

    for line in stdout.decode(errors="replace").splitlines():
        # Line: "Timestamp  A/R Flags  if  Hostname  Address  TTL"
        parts = line.split()
        if len(parts) >= 6 and parts[1] == "Add":
            addr = parts[5]
            if re.match(r'\d+\.\d+\.\d+\.\d+', addr):
                return addr
    return None


def discover_services(service_type: str, timeout: float = 3.0) -> list[dict]:
    if not _DNS_SD:
        raise RuntimeError(
            "mDNS discovery requires dns-sd (macOS built-in). "
            f"On {platform.system()}, provide host and port manually."
        )
    instances = _browse(service_type, timeout)
    results = []
    for name in instances:
        info = _resolve(name, service_type, timeout)
        if info and info["host"]:
            results.append(info)
    return results


def discover_pairing_devices(timeout: float = 3.0) -> list[dict]:
    return discover_services(PAIRING_SERVICE, timeout)


def discover_connect_devices(timeout: float = 3.0) -> list[dict]:
    return discover_services(CONNECT_SERVICE, timeout)
