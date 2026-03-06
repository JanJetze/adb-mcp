import re
import xml.etree.ElementTree as ET


def _parse_bounds(bounds_str: str) -> dict | None:
    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds_str)
    if not m:
        return None
    x1, y1, x2, y2 = int(m[1]), int(m[2]), int(m[3]), int(m[4])
    return {
        "x": x1, "y": y1,
        "w": x2 - x1, "h": y2 - y1,
        "cx": (x1 + x2) // 2, "cy": (y1 + y2) // 2,
    }


def _short_class(full: str) -> str:
    return full.rsplit(".", 1)[-1] if full else ""


def _strip_package_id(resource_id: str) -> str:
    return resource_id.split("/", 1)[-1] if "/" in resource_id else resource_id


def _parse_node(elem: ET.Element, simplified: bool) -> dict | None:
    text = elem.get("text", "")
    desc = elem.get("content-desc", "")
    res_id = _strip_package_id(elem.get("resource-id", ""))
    cls = _short_class(elem.get("class", ""))
    clickable = elem.get("clickable") == "true"
    scrollable = elem.get("scrollable") == "true"
    bounds = _parse_bounds(elem.get("bounds", ""))

    children = []
    for child in elem:
        parsed = _parse_node(child, simplified)
        if parsed is not None:
            children.append(parsed)

    if simplified and not text and not desc and not clickable and not scrollable and not children:
        return None

    node: dict = {}
    if cls:
        node["class"] = cls
    if text:
        node["text"] = text
    if desc:
        node["desc"] = desc
    if res_id:
        node["id"] = res_id
    if clickable:
        node["clickable"] = True
    if scrollable:
        node["scrollable"] = True
    if bounds:
        node["bounds"] = bounds
    if children:
        node["children"] = children

    if simplified and len(node) == 1 and "children" in node:
        if len(children) == 1:
            return children[0]
        return None

    return node


def parse_ui_tree(xml_str: str, simplified: bool = True) -> dict | list:
    xml_str = xml_str.strip()
    if xml_str.startswith("UI hierchary dumped to:"):
        xml_str = xml_str.split("\n", 1)[-1].strip()
    # uiautomator sometimes prefixes output
    start = xml_str.find("<?xml")
    if start == -1:
        start = xml_str.find("<hierarchy")
    if start > 0:
        xml_str = xml_str[start:]

    root = ET.fromstring(xml_str)
    result = _parse_node(root, simplified)
    if result is None:
        return {"children": []}
    return result
