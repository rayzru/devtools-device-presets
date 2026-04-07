# Contributing

Thanks for helping! This project is intentionally **opinionated and small** — it's a curated preset, not a dump of every device.

## Two kinds of contributions

### 1. Preset changes (most valuable)

The preset should reflect **real-world usage**, not "I personally own this phone". Open a [Preset change proposal issue](../../issues/new?template=preset_change.yml) with:

- A stat source (e.g. [StatCounter Global Stats](https://gs.statcounter.com/screen-resolution-stats), Apple/Google support pages, manufacturer specs).
- Why the addition/removal improves coverage of *modern responsive design*, not historical exotica.

Heuristic: if the preset already has a representative for that breakpoint, we probably don't need another one. We aim for ~15 entries, not 50.

### 2. CLI / packaging fixes

Smaller scope: bug fixes, OS compatibility, restore behavior, etc.

## Local development

```bash
git clone https://github.com/rayzru/devtools-device-presets.git
cd devtools-device-presets
python -m pip install -e .
python -m pip install pytest
python -m pytest -v
```

When changing the preset, **edit `src/devtools_device_presets/devices.json`** and then sync the top-level copy:

```bash
cp src/devtools_device_presets/devices.json presets/devices-2026.json
```

The test suite enforces both copies stay identical.

## Releasing (maintainers only)

1. Bump `version` in `pyproject.toml` and `src/devtools_device_presets/__init__.py`.
2. Tag and push: `git tag v0.x.y && git push --tags`.
3. Create a GitHub Release for that tag.
4. The `Publish to PyPI` workflow runs automatically via [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) — no token required.
