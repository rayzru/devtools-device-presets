"""Validate the bundled device preset against the Chrome DevTools schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PRESET = Path(__file__).parent.parent / "src" / "devtools_device_presets" / "devices.json"
TOPLEVEL_PRESET = Path(__file__).parent.parent / "presets" / "devices-2026.json"

REQUIRED_KEYS = {
    "title",
    "type",
    "user-agent",
    "capabilities",
    "screen",
    "modes",
    "show-by-default",
    "dual-screen",
    "foldable-screen",
    "show",
    "user-agent-metadata",
}

VALID_TYPES = {"phone", "tablet", "notebook", "desktop", "unknown"}
VALID_CAPABILITIES = {"mobile", "touch"}
VALID_SHOW = {"Always", "Default", "Never"}


@pytest.fixture(scope="module")
def devices() -> list[dict]:
    return json.loads(PRESET.read_text(encoding="utf-8"))


def test_preset_is_a_list(devices):
    assert isinstance(devices, list)
    assert len(devices) >= 10, "preset should contain a curated set, not be empty"


def test_toplevel_preset_matches_packaged(devices):
    """presets/devices-2026.json must stay in sync with the packaged copy."""
    other = json.loads(TOPLEVEL_PRESET.read_text(encoding="utf-8"))
    assert other == devices, "presets/devices-2026.json drifted from src/.../devices.json"


def test_titles_unique(devices):
    titles = [d["title"] for d in devices]
    assert len(titles) == len(set(titles)), "duplicate titles"


def test_titles_sortable_with_zero_padded_prefix(devices):
    """Titles like '01. ...' guarantee stable sort order in DevTools UI."""
    for d in devices:
        prefix = d["title"].split(".", 1)[0]
        assert prefix.isdigit() and len(prefix) == 2, f"bad prefix: {d['title']}"


@pytest.mark.parametrize("device", json.loads(PRESET.read_text(encoding="utf-8")))
def test_device_shape(device):
    missing = REQUIRED_KEYS - device.keys()
    assert not missing, f"{device.get('title', '?')}: missing keys {missing}"

    assert device["type"] in VALID_TYPES, device["type"]
    assert device["show"] in VALID_SHOW, device["show"]
    assert isinstance(device["capabilities"], list)
    for cap in device["capabilities"]:
        assert cap in VALID_CAPABILITIES, cap

    screen = device["screen"]
    assert {"device-pixel-ratio", "vertical", "horizontal"} <= screen.keys()
    dpr = screen["device-pixel-ratio"]
    assert isinstance(dpr, (int, float)) and 0 < dpr <= 4, f"DPR out of range: {dpr}"

    v, h = screen["vertical"], screen["horizontal"]
    assert v["width"] == h["height"] and v["height"] == h["width"], (
        f"{device['title']}: vertical/horizontal not consistent (rotation flip)"
    )
    assert v["width"] > 0 and v["height"] > 0


@pytest.mark.parametrize("device", json.loads(PRESET.read_text(encoding="utf-8")))
def test_modes_cover_orientations(device):
    """Mobile/tablet must declare both orientations so DevTools rotate works."""
    is_mobile = "mobile" in device["capabilities"]
    orientations = {m["orientation"] for m in device["modes"]}
    if is_mobile:
        assert {"vertical", "horizontal"} <= orientations, (
            f"{device['title']}: mobile/tablet must declare both modes"
        )
    else:
        assert "vertical" in orientations


def test_mobile_devices_have_touch(devices):
    for d in devices:
        if d["type"] in ("phone", "tablet"):
            assert "touch" in d["capabilities"], f"{d['title']} missing touch"
            assert "mobile" in d["capabilities"], f"{d['title']} missing mobile"


def test_desktop_devices_have_no_touch(devices):
    for d in devices:
        if d["type"] in ("notebook", "desktop"):
            assert "touch" not in d["capabilities"], (
                f"{d['title']} desktop should not advertise touch by default"
            )


def test_modern_phone_dpr_is_three(devices):
    """Current iPhone Pro / Android flagships are DPR=3, not 2."""
    phones = [d for d in devices if d["type"] == "phone" and "iPhone" in d["title"]]
    assert phones, "expected at least one iPhone-class entry"
    for p in phones:
        assert p["screen"]["device-pixel-ratio"] == 3, (
            f"{p['title']}: modern iPhone-class should be DPR=3"
        )
