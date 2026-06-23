# Proxy Switcher Pro

Professional proxy management tool with multi-source proxy aggregation, async validation, and Windows system integration.

## Features

- 🌐 **Multi-source proxy aggregation** - Collects proxies from 13 different sources
- ⚡ **Async proxy validation** - Fast parallel proxy verification using ThreadPoolExecutor
- 🔐 **Anonymity detection** - Identifies proxy anonymity levels (elite, anonymous, transparent)
- 🎭 **System proxy injection** - Integrates with Windows registry to apply proxies system-wide
- 📊 **Real-time monitoring** - Live statistics and proxy status tracking
- 💾 **Persistent storage** - JSON-based proxy and settings storage

## Requirements

- Python 3.7+
- PyQt5
- requests
- beautifulsoup4
- loguru (optional, falls back to standard logging)

## Installation

```bash
pip install PyQt5 requests beautifulsoup4 loguru
```

## Usage

```bash
python proxy_switcher.py
```

## Main Functions

- **Grab Proxies** - Fetch proxies from all sources
- **Verify All** - Check proxy status and speed
- **Delete Dead** - Remove non-working proxies
- **Delete Slow** - Remove slow proxies
- **Import** - Import proxies from custom sources
- **Auto Rotate** - Set up automatic proxy rotation
- **Clear All** - Remove all proxies

## Architecture

- `ProxyGrabber` - QThread that fetches and parses proxies from multiple sources
- `ProxyChecker` - QThread that validates proxies asynchronously
- `ProxySwitcherPro` - Main GUI application window

## Configuration

Settings are stored in `~/Documents/ProxySwitcher/settings.json`
Proxies are stored in `~/Documents/ProxySwitcher/proxies.json`

## Version

**v1.0.0** - Professional proxy management application

## License

MIT License
