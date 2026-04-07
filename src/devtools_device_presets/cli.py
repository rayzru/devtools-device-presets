"""
devtools-device-presets — install a curated, modern Chrome DevTools custom device list.

Cross-platform CLI (macOS / Linux / Windows). Zero runtime dependencies.

Usage:
    python -m devtools_device_presets                    # interactive
    python -m devtools_device_presets --all              # apply to every detected profile
    python -m devtools_device_presets --profile "Profile 1" --profile "Profile 6"
    python -m devtools_device_presets --browser chrome --browser edge --all
    python -m devtools_device_presets --custom path/to/devices.json
    python -m devtools_device_presets --restore          # restore the most recent backup
    python -m devtools_device_presets --dry-run          # show what would happen
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PRESET_PATH = Path(__file__).parent / "devices.json"

# DevTools key that holds the JSON-encoded array of custom emulated devices.
# Value is a STRING containing JSON (Chrome stores it that way).
DEVTOOLS_KEY = "custom-emulated-device-list"


@dataclass(frozen=True)
class Browser:
    name: str
    # Per-OS list of candidate "User Data" directories
    user_data_dirs: dict[str, list[Path]]
    process_names: list[str]  # used to detect if running


def _home() -> Path:
    return Path.home()


def _browsers() -> list[Browser]:
    home = _home()
    return [
        Browser(
            name="chrome",
            user_data_dirs={
                "darwin": [home / "Library/Application Support/Google/Chrome"],
                "linux": [
                    home / ".config/google-chrome",
                    home / ".config/google-chrome-beta",
                    home / ".config/chromium",
                ],
                "win32": [
                    Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/User Data",
                ],
            },
            process_names=["Google Chrome", "chrome", "chrome.exe"],
        ),
        Browser(
            name="edge",
            user_data_dirs={
                "darwin": [home / "Library/Application Support/Microsoft Edge"],
                "linux": [home / ".config/microsoft-edge"],
                "win32": [
                    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Edge/User Data",
                ],
            },
            process_names=["Microsoft Edge", "msedge", "msedge.exe"],
        ),
        Browser(
            name="brave",
            user_data_dirs={
                "darwin": [home / "Library/Application Support/BraveSoftware/Brave-Browser"],
                "linux": [home / ".config/BraveSoftware/Brave-Browser"],
                "win32": [
                    Path(os.environ.get("LOCALAPPDATA", ""))
                    / "BraveSoftware/Brave-Browser/User Data",
                ],
            },
            process_names=["Brave Browser", "brave", "brave.exe"],
        ),
    ]


def _platform_key() -> str:
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "darwin":
        return "darwin"
    if sys.platform in ("win32", "cygwin"):
        return "win32"
    return sys.platform


@dataclass(frozen=True)
class ProfileTarget:
    browser: str
    profile_name: str  # e.g. "Default", "Profile 1"
    prefs_path: Path

    @property
    def label(self) -> str:
        return f"{self.browser}: {self.profile_name}"


def discover_profiles(browser_filter: list[str] | None = None) -> list[ProfileTarget]:
    """Find every Chromium-family profile that has a Preferences file."""
    plat = _platform_key()
    targets: list[ProfileTarget] = []
    for b in _browsers():
        if browser_filter and b.name not in browser_filter:
            continue
        for user_data in b.user_data_dirs.get(plat, []):
            if not user_data.exists():
                continue
            for child in sorted(user_data.iterdir()):
                if not child.is_dir():
                    continue
                # Profile dirs are "Default" or "Profile N"
                if child.name != "Default" and not child.name.startswith("Profile "):
                    continue
                prefs = child / "Preferences"
                if prefs.is_file():
                    targets.append(
                        ProfileTarget(browser=b.name, profile_name=child.name, prefs_path=prefs)
                    )
    return targets


def is_browser_running() -> list[str]:
    """Return names of any running Chromium-family browsers (best-effort, no deps)."""
    running: list[str] = []
    try:
        import subprocess

        if sys.platform == "win32":
            out = subprocess.run(
                ["tasklist"], capture_output=True, text=True, check=False
            ).stdout.lower()
            for b in _browsers():
                for proc in b.process_names:
                    if proc.lower() in out:
                        running.append(b.name)
                        break
        else:
            out = subprocess.run(
                ["ps", "-A", "-o", "comm="], capture_output=True, text=True, check=False
            ).stdout
            for b in _browsers():
                for proc in b.process_names:
                    if any(proc in line for line in out.splitlines()):
                        running.append(b.name)
                        break
    except Exception:
        pass
    return sorted(set(running))


def load_preset(custom_path: Path | None) -> str:
    """Return the device list as a JSON-encoded *string* (Chrome stores it that way)."""
    src = custom_path if custom_path else PRESET_PATH
    data = json.loads(src.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{src}: expected a JSON array of device objects")
    # Re-encode compactly to match Chrome's storage style
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


def backup_prefs(prefs_path: Path, ts: str) -> Path:
    backup = prefs_path.with_name(f"{prefs_path.name}.cd2026-backup-{ts}")
    shutil.copy2(prefs_path, backup)
    return backup


def find_latest_backup(prefs_path: Path) -> Path | None:
    candidates = sorted(prefs_path.parent.glob(f"{prefs_path.name}.cd2026-backup-*"))
    return candidates[-1] if candidates else None


def patch_prefs(prefs_path: Path, devices_json_string: str) -> int:
    """Write the device list into Preferences. Returns device count."""
    raw = prefs_path.read_text(encoding="utf-8")
    prefs = json.loads(raw)
    devtools = prefs.setdefault("devtools", {})
    devtools_prefs = devtools.setdefault("preferences", {})
    devtools_prefs[DEVTOOLS_KEY] = devices_json_string
    # Chrome itself stores Preferences as a single-line JSON document.
    prefs_path.write_text(json.dumps(prefs, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    return len(json.loads(devices_json_string))


def restore_prefs(prefs_path: Path) -> Path | None:
    backup = find_latest_backup(prefs_path)
    if not backup:
        return None
    shutil.copy2(backup, prefs_path)
    return backup


def _interactive_select(targets: list[ProfileTarget]) -> list[ProfileTarget]:
    print("\nDetected profiles:")
    for i, t in enumerate(targets, 1):
        print(f"  [{i}] {t.label}")
    print("  [a] all")
    print("  [q] quit")
    raw = input("\nSelect (e.g. 1,3 or a): ").strip().lower()
    if raw in ("q", ""):
        return []
    if raw == "a":
        return list(targets)
    picked: list[ProfileTarget] = []
    for piece in raw.replace(" ", "").split(","):
        if not piece.isdigit():
            continue
        idx = int(piece) - 1
        if 0 <= idx < len(targets):
            picked.append(targets[idx])
    return picked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="devtools-device-presets",
        description="Install a curated 2026 Chrome DevTools custom device list.",
    )
    parser.add_argument(
        "--browser",
        action="append",
        choices=["chrome", "edge", "brave"],
        help="Limit to one or more browsers (default: all detected).",
    )
    parser.add_argument(
        "--profile",
        action="append",
        help='Profile name to target (e.g. "Default", "Profile 1"). Repeatable.',
    )
    parser.add_argument("--all", action="store_true", help="Apply to every detected profile.")
    parser.add_argument("--custom", type=Path, help="Path to a custom devices JSON array.")
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Restore the most recent backup made by this tool.",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would change but write nothing."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip the 'browser is running' safety check (NOT recommended).",
    )
    args = parser.parse_args(argv)

    targets = discover_profiles(browser_filter=args.browser)
    if not targets:
        print("No Chromium-family profiles found on this machine.", file=sys.stderr)
        return 1

    if args.profile:
        wanted = set(args.profile)
        targets = [t for t in targets if t.profile_name in wanted]
        if not targets:
            print(f"None of the requested profiles exist: {sorted(wanted)}", file=sys.stderr)
            return 1
    elif not args.all and sys.stdin.isatty():
        targets = _interactive_select(targets)
    if not targets:
        print("Nothing selected. Aborting.")
        return 0

    # Safety: refuse if a Chromium browser is running unless --force.
    running = is_browser_running()
    if running and not args.force and not args.dry_run:
        print(
            f"\nERROR: these browsers are running and would overwrite our changes on exit: {running}\n"
            "Quit them fully (Cmd+Q / File→Exit), then re-run.\n"
            "Use --force to bypass at your own risk.",
            file=sys.stderr,
        )
        return 2

    if args.restore:
        any_restored = False
        for t in targets:
            backup = find_latest_backup(t.prefs_path) if not args.dry_run else None
            if args.dry_run:
                latest = find_latest_backup(t.prefs_path)
                print(
                    f"[dry-run] {t.label}: would restore from "
                    f"{latest.name if latest else '(no backup found)'}"
                )
                continue
            if backup:
                restore_prefs(t.prefs_path)
                print(f"Restored {t.label} from {backup.name}")
                any_restored = True
            else:
                print(f"SKIP {t.label}: no backup found")
        return 0 if any_restored or args.dry_run else 1

    devices_json_string = load_preset(args.custom)
    device_count = len(json.loads(devices_json_string))
    ts = time.strftime("%Y%m%d-%H%M%S")

    print(f"\nApplying {device_count} devices from {(args.custom or PRESET_PATH).name}")
    for t in targets:
        if args.dry_run:
            print(f"[dry-run] {t.label}: would write {device_count} devices (+ backup)")
            continue
        try:
            backup = backup_prefs(t.prefs_path, ts)
            count = patch_prefs(t.prefs_path, devices_json_string)
            print(f"OK {t.label}: {count} devices  (backup: {backup.name})")
        except Exception as exc:
            print(f"FAIL {t.label}: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
