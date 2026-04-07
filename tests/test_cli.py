"""Smoke + unit tests for the installer CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from devtools_device_presets import cli


def _fake_prefs(tmp_path: Path) -> Path:
    prefs = tmp_path / "Preferences"
    prefs.write_text(
        json.dumps(
            {
                "profile": {"name": "test"},
                "devtools": {"preferences": {"some-other-key": "untouched"}},
            }
        ),
        encoding="utf-8",
    )
    return prefs


def test_load_preset_returns_string():
    s = cli.load_preset(None)
    assert isinstance(s, str)
    devices = json.loads(s)
    assert isinstance(devices, list) and len(devices) >= 10


def test_patch_writes_devtools_key(tmp_path: Path):
    prefs = _fake_prefs(tmp_path)
    devices_str = cli.load_preset(None)
    count = cli.patch_prefs(prefs, devices_str)
    assert count >= 10

    after = json.loads(prefs.read_text(encoding="utf-8"))
    assert after["devtools"]["preferences"][cli.DEVTOOLS_KEY] == devices_str
    # Other keys preserved
    assert after["devtools"]["preferences"]["some-other-key"] == "untouched"
    assert after["profile"]["name"] == "test"


def test_backup_and_restore_roundtrip(tmp_path: Path):
    prefs = _fake_prefs(tmp_path)
    original = prefs.read_text(encoding="utf-8")

    backup = cli.backup_prefs(prefs, "20260101-000000")
    assert backup.exists()
    assert backup.read_text(encoding="utf-8") == original

    cli.patch_prefs(prefs, cli.load_preset(None))
    assert prefs.read_text(encoding="utf-8") != original

    restored = cli.restore_prefs(prefs)
    assert restored == backup
    assert prefs.read_text(encoding="utf-8") == original


def test_find_latest_backup_picks_newest(tmp_path: Path):
    prefs = _fake_prefs(tmp_path)
    cli.backup_prefs(prefs, "20260101-000000")
    cli.backup_prefs(prefs, "20260301-120000")
    cli.backup_prefs(prefs, "20260201-000000")
    latest = cli.find_latest_backup(prefs)
    assert latest is not None and "20260301-120000" in latest.name


def test_discover_returns_profiles_when_present(tmp_path: Path, monkeypatch):
    """Auto-discover should pick up Default and Profile N directories."""
    fake_user_data = tmp_path / "Chrome"
    for name in ["Default", "Profile 1", "Profile 2", "System Profile", "not-a-profile"]:
        d = fake_user_data / name
        d.mkdir(parents=True)
        if name in ("Default", "Profile 1", "Profile 2"):
            (d / "Preferences").write_text("{}", encoding="utf-8")

    fake_browser = cli.Browser(
        name="chrome",
        user_data_dirs={
            "darwin": [fake_user_data],
            "linux": [fake_user_data],
            "win32": [fake_user_data],
        },
        process_names=["chrome"],
    )
    monkeypatch.setattr(cli, "_browsers", lambda: [fake_browser])

    targets = cli.discover_profiles()
    names = sorted(t.profile_name for t in targets)
    assert names == ["Default", "Profile 1", "Profile 2"]


def test_dry_run_does_not_modify(tmp_path: Path, monkeypatch, capsys):
    prefs = _fake_prefs(tmp_path)
    before = prefs.read_text(encoding="utf-8")

    fake_user_data = tmp_path
    fake_profile = tmp_path / "Profile X"
    fake_profile.mkdir()
    (fake_profile / "Preferences").write_text(before, encoding="utf-8")

    fake_browser = cli.Browser(
        name="chrome",
        user_data_dirs={k: [fake_user_data] for k in ("darwin", "linux", "win32")},
        process_names=["__none__"],
    )
    monkeypatch.setattr(cli, "_browsers", lambda: [fake_browser])
    monkeypatch.setattr(cli, "is_browser_running", lambda: [])

    rc = cli.main(["--all", "--dry-run"])
    assert rc == 0
    assert (fake_profile / "Preferences").read_text(encoding="utf-8") == before
    out = capsys.readouterr().out
    assert "[dry-run]" in out


def test_refuses_when_browser_running(tmp_path: Path, monkeypatch, capsys):
    fake_profile = tmp_path / "Default"
    fake_profile.mkdir()
    (fake_profile / "Preferences").write_text("{}", encoding="utf-8")

    fake_browser = cli.Browser(
        name="chrome",
        user_data_dirs={k: [tmp_path] for k in ("darwin", "linux", "win32")},
        process_names=["chrome"],
    )
    monkeypatch.setattr(cli, "_browsers", lambda: [fake_browser])
    monkeypatch.setattr(cli, "is_browser_running", lambda: ["chrome"])

    rc = cli.main(["--all"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "running" in err.lower()
