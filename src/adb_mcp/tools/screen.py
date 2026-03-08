import base64
import io
import json

from adb_mcp.adb import adb_exec, adb_exec_binary
from adb_mcp.parsers.ui_tree import parse_ui_tree


def screenshot(max_width: int = 540) -> tuple[str, str]:
    """Returns (base64_png, mime_type)."""
    png_data = adb_exec_binary("exec-out", "screencap", "-p", timeout=15)
    if not png_data:
        raise RuntimeError("Empty screenshot data")

    if max_width and max_width > 0:
        from PIL import Image
        img = Image.open(io.BytesIO(png_data))
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            png_data = buf.getvalue()

    return base64.b64encode(png_data).decode("ascii"), "image/png"


def ui_tree(simplified: bool = True) -> str:
    xml_output = adb_exec("exec-out", "uiautomator", "dump", "/dev/tty", timeout=15)
    parsed = parse_ui_tree(xml_output, simplified=simplified)
    return json.dumps(parsed, indent=2)
