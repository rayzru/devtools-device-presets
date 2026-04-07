# devtools-device-presets

> A curated, opinionated **2026 device preset** for Chrome DevTools — modern viewports backed by global usage statistics, with clear rationale for every entry. Compatible with [Vibranium](https://github.com/Pittan/vibranium), plus a zero-dependency Python installer.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Why this exists

Chrome DevTools ships with a default device list that has barely changed in years and still includes phones nobody uses anymore (Galaxy Note 3, Blackberry PlayBook). Most developers either:

1. Use the stale defaults and miss real-world breakpoints, or
2. Add a few personal devices and never sync them across machines/teammates, or
3. Copy/paste from a giant list of every phone ever made (200+ entries — useless noise).

This repo is the **third option**: a small, opinionated, **15-device** preset where every entry is justified by global usage data and modern responsive-design needs — not a dump of every phone ever made.

## What's in the preset

15 devices, each with both portrait and landscape orientations (DevTools' rotate button handles flipping — no duplicate entries).

### 📱 Mobile (6)

| # | Name | Viewport | DPR | Rationale |
|---|---|---|---|---|
| 1 | Foldable Cover | 280×653 | 3 | Galaxy Z Fold cover screen — narrowest viewport you should still test |
| 2 | Android Common | 360×800 | 3 | **#1 mobile viewport globally** ([StatCounter Mar 2026](https://gs.statcounter.com/screen-resolution-stats/mobile/worldwide)) |
| 3 | Android Tall | 384×832 | 3 | Tall Android flagships (Samsung S-series et al.) |
| 4 | iPhone Base | 390×844 | 3 | iPhone 12–15 base models |
| 5 | iPhone Pro | 393×873 | 3 | iPhone 14/15/16 Pro |
| 6 | Phone Large | 414×896 | 3 | iPhone Plus, large Android |

### 📱 Tablet (3)

| # | Name | Viewport | DPR | Rationale |
|---|---|---|---|---|
| 7 | iPad Legacy | 768×1024 | 2 | **#1 tablet viewport globally** ([StatCounter Feb 2026](https://gs.statcounter.com/screen-resolution-stats/tablet/worldwide)) |
| 8 | iPad Modern | 820×1180 | 2 | Modern iPad / iPad Air |
| 9 | Android Tablet | 800×1280 | 2 | Galaxy Tab and similar |

### 💻 Desktop (6)

| # | Name | Viewport | DPR | Rationale |
|---|---|---|---|---|
| 10 | Laptop Small | 1366×768 | 1 | Still common on budget Windows laptops |
| 11 | Windows 125% scale | 1536×864 | 1.25 | 1920×1080 with the Windows default 125% scaling — extremely common |
| 12 | MacBook Retina | 1440×900 | 2 | MacBook Air/Pro default looks-like resolution |
| 13 | Desktop FHD | 1920×1080 | 1 | Baseline desktop |
| 14 | Desktop QHD | 2560×1440 | 1 | 27" QHD monitors |
| 15 | Ultrawide 21:9 | 3440×1440 | 1 | Ultrawide gaming/dev monitors — edge case |

### Design decisions

- **Generic viewports, not exhaustive device list.** Real-world responsive design fails at *breakpoints*, not at exact device pixels. 15 well-chosen viewports beat 200 noisy entries.
- **Explicit DPR on desktop.** A bug that only shows on Retina is invisible on a non-Retina dev machine. Setting DPR explicitly makes screenshots reproducible across teammates.
- **DPR=3 on modern mobile.** All current iPhone Pro and most flagship Android use DPR=3, not 2. This matters for hairline borders, image sharpness, and `1px` rendering.
- **Both orientations baked in.** Each device declares both `vertical` and `horizontal` modes, so the DevTools rotate button works without duplicate entries.
- **Plausible UA / UA-CH metadata.** Filled with generic-but-current values (Chrome 147, Safari 26, iOS 26, macOS Tahoe). Helpful when you do have UA-aware code, harmless otherwise.
- **Foldable + ultrawide as edges.** Not because they're common, but because they're the cheapest way to surface broken layouts.

> Sources: [StatCounter Global Stats](https://gs.statcounter.com/screen-resolution-stats), Chrome DevTools [Device Mode docs](https://developer.chrome.com/docs/devtools/device-mode/), Wikipedia version histories.

---

## Installation

You have three options. Pick whichever fits.

### Option A — Zero-deps Python installer (recommended)

Works on macOS, Linux, Windows. Requires only Python 3.9+ (already on macOS/Linux; one-time install on Windows).

```bash
git clone https://github.com/rayzru/devtools-device-presets.git
cd devtools-device-presets

# Quit Chrome FULLY first (Cmd+Q on macOS, File→Exit on Windows/Linux).

python -m devtools_device_presets               # interactive: pick profiles
python -m devtools_device_presets --all         # apply to every detected profile
python -m devtools_device_presets --dry-run     # preview, no writes
```

Restore the most recent backup at any time:

```bash
python -m devtools_device_presets --restore --all
```

#### Features

- Auto-detects **Chrome, Edge, Brave** profiles on **macOS / Linux / Windows**
- Creates a timestamped backup before every write (`Preferences.cd2026-backup-YYYYMMDD-HHMMSS`)
- Refuses to run if a Chromium browser is open (would otherwise be overwritten on exit) — bypass with `--force`
- `--restore` rolls back to the most recent backup
- `--custom path/to/your.json` lets you install your own preset
- Filter by `--browser chrome` or `--profile "Profile 1"` (repeatable)

### Option B — Vibranium (if you already have Node.js)

[Vibranium](https://github.com/Pittan/vibranium) is an existing, well-maintained CLI for managing DevTools devices. Our preset is a valid Vibranium input.

```bash
npm install -g @pittankopta/vibranium
vibranium add presets/devices-2026.json
```

### Option C — Manual

1. Quit Chrome fully.
2. Open `presets/devices-2026.json` in this repo.
3. Find your `Preferences` file:
   - **macOS**: `~/Library/Application Support/Google/Chrome/<Profile>/Preferences`
   - **Linux**: `~/.config/google-chrome/<Profile>/Preferences`
   - **Windows**: `%LOCALAPPDATA%\Google\Chrome\User Data\<Profile>\Preferences`
4. Find or add the key `devtools.preferences.custom-emulated-device-list` and paste the JSON **as a single string** (Chrome stores it that way).
5. Save and reopen Chrome → DevTools → Settings → Devices.

---

## Comparison to existing tools

| Project | Curated preset | Installer | Multi-browser | Active in 2026 |
|---|---|---|---|---|
| **devtools-device-presets** (this) | ✅ opinionated 15-device | ✅ zero-deps Python | ✅ Chrome/Edge/Brave | ✅ |
| [Pittan/vibranium](https://github.com/Pittan/vibranium) | ❌ bring-your-own JSON | ✅ Node.js CLI | ✅ | ✅ |
| [alxwndr/list-of-custom-emulated-devices-in-chrome](https://github.com/alxwndr/list-of-custom-emulated-devices-in-chrome) | ✅ huge dump | ❌ manual paste | — | ❌ |

**Vibranium** is the established CLI for *transport*. This repo is the curated *content* — and is intentionally compatible with Vibranium so you can use both.

---

## Why not a Chrome extension?

Short version: it's not technically possible.

The custom device list lives in the Chrome profile's `Preferences` file under a key managed by the DevTools frontend. Extensions:

- Have **no `chrome.devtools.emulation` API** — Chromium does not expose the emulated device list to extension code.
- Cannot modify `Preferences` directly — Chrome holds it in memory and re-serializes on exit, overwriting any external change.
- Cannot inject UI into DevTools' own settings panes.

The CDP `Emulation.setDeviceMetricsOverride` call (available via the `debugger` permission) is **per-tab and ephemeral** — it does not register a saved device. The only stable distribution path is editing `Preferences` while the browser is closed, which requires native filesystem access — i.e. a CLI or a managed enterprise policy.

---

## Refresh policy

The preset is updated annually as device share shifts. Each release tags the data sources used. PRs welcome with stat-backed additions or removals.

---

## License

MIT — see [LICENSE](LICENSE).

## Credits

- [StatCounter Global Stats](https://gs.statcounter.com/) — viewport share data
- [Chrome DevTools](https://developer.chrome.com/docs/devtools/) — the underlying feature
- [Vibranium](https://github.com/Pittan/vibranium) — the existing CLI this preset is compatible with
