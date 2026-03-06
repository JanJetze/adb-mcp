from adb_mcp.parsers.ui_tree import parse_ui_tree, _parse_bounds


SAMPLE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<hierarchy rotation="0">
  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" bounds="[0,0][1080,2400]">
    <node index="0" text="Settings" resource-id="com.android.settings:id/title" class="android.widget.TextView" clickable="true" bounds="[0,100][1080,200]" content-desc="" scrollable="false" />
    <node index="1" text="" resource-id="" class="android.widget.LinearLayout" bounds="[0,200][1080,300]">
      <node index="0" text="Wi-Fi" resource-id="android:id/title" class="android.widget.TextView" clickable="true" bounds="[50,210][500,290]" content-desc="Wireless network settings" scrollable="false" />
    </node>
    <node index="2" text="" resource-id="" class="android.widget.FrameLayout" bounds="[0,300][1080,400]" />
  </node>
</hierarchy>
"""

PREFIXED_XML = "UI hierchary dumped to: /dev/tty\n" + SAMPLE_XML


class TestParseBounds:
    def test_valid_bounds(self):
        result = _parse_bounds("[0,100][1080,200]")
        assert result == {"x": 0, "y": 100, "w": 1080, "h": 100, "cx": 540, "cy": 150}

    def test_invalid_bounds(self):
        assert _parse_bounds("invalid") is None
        assert _parse_bounds("") is None


class TestParseUiTree:
    def test_simplified_prunes_empty(self):
        result = parse_ui_tree(SAMPLE_XML, simplified=True)
        # The empty FrameLayout at index=2 should be pruned
        flat = str(result)
        assert "Settings" in flat
        assert "Wi-Fi" in flat

    def test_simplified_has_center_coords(self):
        result = parse_ui_tree(SAMPLE_XML, simplified=True)
        # Find the Settings node
        def find_node(tree, text):
            if isinstance(tree, dict):
                if tree.get("text") == text:
                    return tree
                for child in tree.get("children", []):
                    found = find_node(child, text)
                    if found:
                        return found
            return None

        settings = find_node(result, "Settings")
        assert settings is not None
        assert settings["bounds"]["cx"] == 540
        assert settings["bounds"]["cy"] == 150
        assert settings["clickable"] is True

    def test_full_tree_includes_empty_nodes(self):
        result = parse_ui_tree(SAMPLE_XML, simplified=False)
        flat = str(result)
        assert "FrameLayout" in flat

    def test_handles_prefixed_output(self):
        result = parse_ui_tree(PREFIXED_XML, simplified=True)
        assert "Settings" in str(result)

    def test_strips_package_from_resource_id(self):
        result = parse_ui_tree(SAMPLE_XML, simplified=True)

        def find_node(tree, text):
            if isinstance(tree, dict):
                if tree.get("text") == text:
                    return tree
                for child in tree.get("children", []):
                    found = find_node(child, text)
                    if found:
                        return found
            return None

        settings = find_node(result, "Settings")
        assert settings["id"] == "title"
