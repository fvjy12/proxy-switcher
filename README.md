# Proxy Switcher Pro

Professional proxy management tool with multi-source proxy aggregation, async validation, and Windows system integration.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.7%2B-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## Features

- 🌐 **Multi-source proxy aggregation** - Collects proxies from 13 different sources
- ⚡ **Async proxy validation** - Fast parallel proxy verification using ThreadPoolExecutor
- 🔐 **Anonymity detection** - Identifies proxy anonymity levels (elite, anonymous, transparent)
- 🎭 **System proxy injection** - Integrates with Windows registry to apply proxies system-wide
- 📊 **Real-time monitoring** - Live statistics and proxy status tracking
- 💾 **Persistent storage** - JSON-based proxy and settings storage
- 🎨 **Black & White design** - Professional dark theme with clean monochrome interface
- ⭐ **Favorites** - Mark important proxies as favorites
- 🔄 **Auto-rotation** - Automatically rotate proxies at configurable intervals
- 📋 **Clipboard support** - Copy proxy addresses with one click

## Requirements

- Python 3.7+
- PyQt5
- requests
- beautifulsoup4
- loguru (optional, falls back to standard logging)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/proxy-switcher-pro.git
cd proxy-switcher-pro

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python proxy_switcher.py
```

## Main Functions

| Function | Description |
|----------|-------------|
| **Grab Proxies** | Fetch proxies from all 13 sources |
| **Verify All** | Check proxy status and speed in parallel |
| **Delete Dead** | Remove non-working proxies |
| **Delete Slow** | Remove proxies slower than a threshold |
| **Import** | Import proxies from text, JSON, CSV, or URL |
| **Auto Rotate** | Set up automatic proxy rotation |
| **Clear All** | Remove all proxies |

## Architecture

```
proxy_switcher.py          # Main application (GUI)
import.py                  # Proxy import utilities
requirements.txt           # Python dependencies
```

### Core Classes

- `ProxyGrabber` - QThread that fetches and parses proxies from multiple sources
- `ProxyChecker` - QThread that validates proxies asynchronously
- `ProxySwitcherPro` - Main GUI application window
- `Theme` - Black & White theme constants and stylesheet
- `SplashScreen` - Application splash screen

## Configuration

Settings are stored in `~/Documents/ProxySwitcher/settings.json`
Proxies are stored in `~/Documents/ProxySwitcher/proxies.json`
Logs are stored in `~/Documents/ProxySwitcher/logs/`

## Import Module

The `import.py` module provides functions for importing proxies from various sources:

```python
from import import import_from_text, import_from_file, import_from_url

# Import from text
proxies = import_from_text("192.168.1.1:8080\n10.0.0.1:3128")

# Import from file (txt, json, csv)
proxies = import_from_file("proxies.txt")

# Import from URL
proxies = import_from_url("https://example.com/proxies.txt")
```

## Platform Support

- **Windows** - Full support including system proxy configuration
- **Linux/macOS** - GUI works, but system proxy configuration is not available

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
