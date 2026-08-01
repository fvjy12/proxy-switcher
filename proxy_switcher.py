#!/usr/bin/env python3
"""
Proxy Switcher Pro - Professional Proxy Management Tool
Version 2.0.0

Features:
- Multi-source proxy aggregation
- Async proxy validation and verification
- System-level proxy configuration
- Real-time proxy monitoring and metrics
- Black & White professional design
"""
import sys
import os
import json
import socket
import threading
import time
import re
import random
import platform
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import requests
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# ============================================================================
# Logging Configuration
# ============================================================================
try:
    from loguru import logger
    LOGURU_AVAILABLE = True
except ImportError:
    LOGURU_AVAILABLE = False
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    _std_logger = logging.getLogger("ProxySwitcher")

    class LoggerAdapter:
        def __init__(self, logger_obj):
            self._logger = logger_obj
        def info(self, msg):
            self._logger.info(msg)
        def error(self, msg):
            self._logger.error(msg)
        def warning(self, msg):
            self._logger.warning(msg)
        def debug(self, msg):
            self._logger.debug(msg)

    logger = LoggerAdapter(_std_logger)

if LOGURU_AVAILABLE:
    try:
        LOG_DIR = Path.home() / "Documents" / "ProxySwitcher" / "logs"
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        logger.remove()
        logger.add(
            sys.stderr,
            format="<level>{time:HH:mm:ss}</level> | <level>{level: <8}</level> | {message}",
            level="INFO",
            colorize=True
        )
        logger.add(
            LOG_DIR / "proxy_switcher_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            rotation="500 MB",
            retention="10 days",
            level="DEBUG"
        )
    except Exception:
        pass

logger.info("=" * 70)
logger.info("Proxy Switcher Pro v2.0.0 - Starting Application")
logger.info("Loading modules: requests, BeautifulSoup, PyQt5...")
logger.info("=" * 70)

# ============================================================================
# Application Configuration
# ============================================================================
APP_NAME = "Proxy Switcher Pro"
VERSION = "2.0.0"
CONFIG_DIR = Path.home() / "Documents" / "ProxySwitcher"
CONFIG_FILE = CONFIG_DIR / "proxies.json"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

IS_WINDOWS = platform.system() == "Windows"

logger.info("Initializing configuration directory")
try:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Config directory: {CONFIG_DIR}")
except Exception as e:
    logger.error(f"Configuration error: {e}")

# Proxy Sources
PROXY_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all&format=textplain",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://www.sslproxies.org/",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=all&ssl=all&anonymity=all&format=textplain",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/Socks5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/Socks4.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt",
]

logger.info(f"Loaded {len(PROXY_SOURCES)} proxy sources")


# ============================================================================
# Black & White Theme
# ============================================================================
class Theme:
    """Black & White professional theme constants"""
    BG = "#1a1a1a"
    BG_ALT = "#2d2d2d"
    BG_HOVER = "#3d3d3d"
    FG = "#ffffff"
    FG_DIM = "#aaaaaa"
    FG_DARK = "#666666"
    BORDER = "#444444"
    ACCENT = "#ffffff"
    ACCENT_HOVER = "#cccccc"
    ACCENT_PRESSED = "#999999"
    SUCCESS = "#4caf50"
    WARNING = "#ff9800"
    ERROR = "#f44336"
    INFO = "#2196f3"
    SELECTION = "#555555"
    HEADER_BG = "#2d2d2d"
    HEADER_FG = "#ffffff"

    @staticmethod
    def stylesheet() -> str:
        return f"""
            QMainWindow, QDialog {{
                background-color: {Theme.BG};
            }}
            QWidget {{
                background-color: {Theme.BG};
                color: {Theme.FG};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QLabel {{
                color: {Theme.FG};
            }}
            QLabel#title {{
                font-size: 16px;
                font-weight: bold;
                color: {Theme.FG};
            }}
            QLabel#subtitle {{
                font-size: 11px;
                color: {Theme.FG_DIM};
            }}
            QLabel#stats {{
                font-size: 11px;
                color: {Theme.FG_DIM};
                padding: 4px;
            }}
            QPushButton {{
                background-color: {Theme.BG_ALT};
                color: {Theme.FG};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_HOVER};
                border-color: {Theme.FG_DIM};
            }}
            QPushButton:pressed {{
                background-color: {Theme.BG};
            }}
            QPushButton:disabled {{
                background-color: {Theme.BG};
                color: {Theme.FG_DARK};
                border-color: {Theme.BORDER};
            }}
            QPushButton#primary {{
                background-color: {Theme.FG};
                color: {Theme.BG};
                border: none;
            }}
            QPushButton#primary:hover {{
                background-color: {Theme.ACCENT_HOVER};
            }}
            QPushButton#danger {{
                background-color: {Theme.BG_ALT};
                color: {Theme.ERROR};
                border: 1px solid {Theme.ERROR};
            }}
            QPushButton#danger:hover {{
                background-color: {Theme.ERROR};
                color: {Theme.FG};
            }}
            QPushButton#success {{
                background-color: {Theme.BG_ALT};
                color: {Theme.SUCCESS};
                border: 1px solid {Theme.SUCCESS};
            }}
            QPushButton#success:hover {{
                background-color: {Theme.SUCCESS};
                color: {Theme.BG};
            }}
            QTableWidget {{
                background-color: {Theme.BG};
                alternate-background-color: {Theme.BG_ALT};
                gridline-color: {Theme.BORDER};
                border: 1px solid {Theme.BORDER};
                color: {Theme.FG};
                selection-background-color: {Theme.SELECTION};
                selection-color: {Theme.FG};
            }}
            QTableWidget::item {{
                padding: 6px;
                border: none;
            }}
            QTableWidget::item:selected {{
                background-color: {Theme.SELECTION};
                color: {Theme.FG};
            }}
            QHeaderView::section {{
                background-color: {Theme.HEADER_BG};
                color: {Theme.HEADER_FG};
                padding: 8px;
                border: 1px solid {Theme.BORDER};
                font-weight: bold;
            }}
            QProgressBar {{
                border: 1px solid {Theme.BORDER};
                border-radius: 3px;
                background-color: {Theme.BG_ALT};
                text-align: center;
                color: {Theme.FG};
                height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {Theme.FG};
                border-radius: 2px;
            }}
            QScrollBar:vertical {{
                width: 12px;
                background-color: {Theme.BG};
            }}
            QScrollBar::handle:vertical {{
                background-color: {Theme.BG_HOVER};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {Theme.FG_DIM};
            }}
            QScrollBar:horizontal {{
                height: 12px;
                background-color: {Theme.BG};
            }}
            QScrollBar::handle:horizontal {{
                background-color: {Theme.BG_HOVER};
                border-radius: 6px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {Theme.FG_DIM};
            }}
            QMenu {{
                background-color: {Theme.BG_ALT};
                color: {Theme.FG};
                border: 1px solid {Theme.BORDER};
            }}
            QMenu::item {{
                padding: 8px 24px;
            }}
            QMenu::item:selected {{
                background-color: {Theme.BG_HOVER};
            }}
            QSpinBox, QDoubleSpinBox, QLineEdit, QTextEdit {{
                background-color: {Theme.BG_ALT};
                color: {Theme.FG};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 6px;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus, QTextEdit:focus {{
                border-color: {Theme.FG_DIM};
            }}
            QCheckBox {{
                color: {Theme.FG};
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {Theme.BORDER};
                background-color: {Theme.BG_ALT};
            }}
            QCheckBox::indicator:checked {{
                background-color: {Theme.FG};
                border-color: {Theme.FG};
            }}
            QMessageBox {{
                background-color: {Theme.BG};
            }}
            QStatusBar {{
                background-color: {Theme.BG_ALT};
                color: {Theme.FG_DIM};
            }}
            QToolTip {{
                background-color: {Theme.BG_ALT};
                color: {Theme.FG};
                border: 1px solid {Theme.BORDER};
            }}
        """


class SplashScreen(QWidget):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        screen = QApplication.primaryScreen()
        self.setGeometry(screen.geometry())

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {Theme.BG};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        title = QLabel("Proxy Switcher Pro")
        title.setFont(QFont("Segoe UI", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {Theme.FG};")
        layout.addWidget(title)

        version = QLabel("v2.0.0")
        version.setFont(QFont("Segoe UI", 14))
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet(f"color: {Theme.FG_DIM};")
        layout.addWidget(version)

        layout.addSpacing(20)

        self.status = QLabel("Initializing...")
        self.status.setFont(QFont("Segoe UI", 12))
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet(f"color: {Theme.FG_DIM};")
        layout.addWidget(self.status)

        self.progress = QProgressBar()
        self.progress.setMaximumWidth(400)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {Theme.BORDER};
                border-radius: 3px;
                background: {Theme.BG_ALT};
            }}
            QProgressBar::chunk {{
                background: {Theme.FG};
                border-radius: 2px;
            }}
        """)
        layout.addWidget(self.progress, alignment=Qt.AlignCenter)

        layout.addStretch()

        self.setWindowTitle("Proxy Switcher Pro")
        self.progress_value = 0
        self.animate()

    def animate(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(50)

    def update_progress(self):
        self.progress_value += 1

        statuses = [
            "Loading configuration...",
            "Initializing proxy system...",
            "Loading UI components...",
            "Preparing main window...",
            "Ready",
        ]
        status_idx = min(self.progress_value // 20, len(statuses) - 1)
        self.status.setText(statuses[status_idx])

        self.progress.setValue(min(self.progress_value, 100))

        if self.progress_value >= 100:
            self.timer.stop()
            QTimer.singleShot(300, self.close_splash)

    def close_splash(self):
        self.close()
        self.finished.emit()


class ProxyGrabber(QThread):
    progress = pyqtSignal(int, str)
    proxy_found = pyqtSignal(str, str, str)
    finished = pyqtSignal(list)

    def __init__(self, max_proxies=100):
        super().__init__()
        self.max_proxies = max_proxies
        self._is_running = True
        self.found_proxies = []
        self.seen = set()
        logger.info(f"[ GRABBER ] Initialized (max_nodes={max_proxies})")

    def stop(self):
        self._is_running = False
        logger.info("[ GRABBER ] Process stopped")

    def fetch_url(self, url, timeout=10) -> Optional[str]:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            logger.debug(f"[ FETCH ] {url}")
            return response.text
        except requests.exceptions.Timeout:
            logger.warning(f"[ TIMEOUT ] {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning(f"[ CONN_ERR ] {url}")
            return None
        except Exception as e:
            logger.error(f"[ FETCH_ERR ] {url}: {e}")
            return None

    def parse_table_proxies(self, html) -> List[Tuple[str, str]]:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('table')
            if not table:
                return []
            proxies = []
            rows = table.find_all('tr')[1:]
            for row in rows:
                try:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        ip = cols[0].text.strip()
                        port = cols[1].text.strip()
                        if ip and port and self.is_valid_ip(ip) and port.isdigit():
                            proxies.append((ip, port))
                except Exception:
                    continue
            logger.info(f"[ PARSE_TABLE ] {len(proxies)} proxies from table")
            return proxies
        except Exception as e:
            logger.error(f"[ PARSE_ERR ] {e}")
            return []

    def is_valid_ip(self, ip: str) -> bool:
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            return all(0 <= int(part) <= 255 for part in parts)
        except Exception:
            return False

    def parse_text_proxies(self, text: str) -> List[Tuple[str, str]]:
        try:
            if not text:
                return []
            proxies = []
            pattern = r'(\d+\.\d+\.\d+\.\d+):(\d+)'
            matches = re.findall(pattern, text)
            for ip, port in matches:
                try:
                    if self.is_valid_ip(ip) and 1 <= int(port) <= 65535:
                        proxies.append((ip, port))
                except Exception:
                    continue
            logger.info(f"[ PARSE_TEXT ] {len(proxies)} proxies from text")
            return proxies
        except Exception as e:
            logger.error(f"[ PARSE_ERR ] {e}")
            return []

    def add_proxy(self, ip: str, port: str, proxy_type: str = 'HTTP'):
        if len(self.found_proxies) >= self.max_proxies:
            self.stop()
            return
        key = f"{ip}:{port}"
        if key not in self.seen:
            self.seen.add(key)
            self.found_proxies.append({
                'ip': ip,
                'port': port,
                'type': proxy_type.upper(),
                'name': f"Proxy_{ip}",
                'login': '',
                'password': '',
                'status': 'fresh',
                'speed': '',
                'anonymity': 'unknown',
                'country': '🌍',
            })
            self.proxy_found.emit(ip, port, proxy_type)
            logger.debug(f"[ NODE_ADD ] {ip}:{port} ({proxy_type})")

    def run(self):
        logger.info(f"[ GRABBER ] Starting collection from {len(PROXY_SOURCES)} sources")
        total_sources = len(PROXY_SOURCES)

        for i, url in enumerate(PROXY_SOURCES):
            if not self._is_running or len(self.found_proxies) >= self.max_proxies:
                break
            progress = int((i / total_sources) * 100)
            msg = f"Collecting... {len(self.found_proxies)}/{self.max_proxies}"
            self.progress.emit(progress, msg)

            # Determine proxy type by URL
            if 'socks5' in url.lower():
                proxy_type = 'SOCKS5'
            elif 'socks4' in url.lower():
                proxy_type = 'SOCKS4'
            else:
                proxy_type = 'HTTP'

            try:
                content = self.fetch_url(url)
                if not content:
                    continue
                if '<table' in content.lower():
                    proxies = self.parse_table_proxies(content)
                else:
                    proxies = self.parse_text_proxies(content)
                for ip, port in proxies:
                    if len(self.found_proxies) >= self.max_proxies:
                        break
                    self.add_proxy(ip, port, proxy_type)
            except Exception as e:
                logger.error(f"[ SOURCE_ERR ] {url}: {e}")
                continue

        logger.info(f"[ GRABBER_DONE ] Collected {len(self.found_proxies)} proxy nodes")
        self.progress.emit(100, f"Done: {len(self.found_proxies)} proxies")
        self.finished.emit(self.found_proxies)


# ============================================================================
# Proxy Checker (Advanced Node Validation System)
# ============================================================================
class ProxyChecker(QThread):
    progress = pyqtSignal(int, str)
    proxy_checked = pyqtSignal(int, dict)
    finished = pyqtSignal(list)
    ip_checked_signal = pyqtSignal(str)

    def __init__(self, proxies, settings):
        super().__init__()
        self.proxies = proxies
        self.settings = settings
        self._is_running = True
        logger.info(f"[ CHECKER ] Initialized for {len(proxies)} nodes")

    def stop(self):
        self._is_running = False
        logger.info("[ CHECKER ] Verification process stopped")

    def check_single_proxy(self, proxy: Dict, index: int) -> Dict:
        results = {
            'status': 'dead',
            'speed': 0,
            'anonymity': 'unknown',
            'country': '🌍',
            'error': ''
        }

        ip = proxy.get('ip', '')
        port = proxy.get('port', '')
        proxy_type = proxy.get('type', 'HTTP').upper()

        if not ip or not port:
            return results

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, int(port)))
            sock.close()

            if result != 0:
                return results
        except Exception:
            return results

        # Check HTTP/HTTPS proxies
        if proxy_type in ['HTTP', 'HTTPS']:
            try:
                proxy_str = f"http://{ip}:{port}"
                proxies_dict = {'http': proxy_str, 'https': proxy_str}

                start = time.time()
                response = requests.get(
                    'http://httpbin.org/ip',
                    proxies=proxies_dict,
                    timeout=3,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                response_time = time.time() - start

                if response.status_code == 200:
                    results['status'] = 'alive'
                    results['speed'] = round(response_time, 2)
                    try:
                        data = response.json()
                        proxy_ip = data.get('origin', '')
                        results['anonymity'] = 'transparent' if proxy_ip == ip else 'elite'
                    except Exception:
                        results['anonymity'] = 'anonymous'
                else:
                    results['status'] = 'slow'
                    results['speed'] = round(response_time, 2)
                    results['error'] = f'HTTP {response.status_code}'

            except requests.exceptions.Timeout:
                results['status'] = 'slow'
                results['speed'] = 3.0
                results['error'] = 'Timeout'
            except requests.exceptions.ConnectionError:
                results['status'] = 'dead'
                results['error'] = 'Connection Error'
            except Exception as e:
                results['status'] = 'dead'
                results['error'] = str(e)[:30]

        # For SOCKS proxies check only availability
        elif proxy_type in ['SOCKS4', 'SOCKS5']:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                start = time.time()
                result = sock.connect_ex((ip, int(port)))
                sock.close()
                response_time = time.time() - start

                if result == 0:
                    results['status'] = 'alive'
                    results['speed'] = round(response_time, 2)
                    results['anonymity'] = 'elite'
                else:
                    results['status'] = 'slow'
                    results['speed'] = 2.0
            except Exception:
                results['status'] = 'dead'

        # Determine country - best service with multiple attempts
        country = self._get_country_by_ip(ip)
        results['country'] = country

        return results

    def _get_country_by_ip(self, ip: str) -> str:
        """[ GEO ] Determines country by IP using multiple sources"""
        # Attempt 1: ip-api.com
        try:
            response = requests.get(f'http://ip-api.com/json/{ip}', timeout=1)
            if response.status_code == 200:
                country = response.json().get('country')
                if country:
                    return country[:2]
        except Exception:
            pass

        # Attempt 2: ipapi.co
        try:
            response = requests.get(f'https://ipapi.co/{ip}/json/', timeout=1)
            if response.status_code == 200:
                country = response.json().get('country_code')
                if country:
                    return country
        except Exception:
            pass

        # Attempt 3: ipstack (if available)
        try:
            response = requests.get(f'http://geoip.vbb.app/{ip}', timeout=1)
            if response.status_code == 200:
                country = response.json().get('country_code')
                if country:
                    return country
        except Exception:
            pass

        return '🌍'  # Default if unable to determine

    def run(self):
        total = len(self.proxies)
        logger.info(f"[ CHECKER ] Starting verification of {total} nodes (ThreadPool)")

        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=2)
            real_ip = response.json().get('ip', 'Unknown')
            logger.info(f"[ HOST_IP ] {real_ip}")
            self.ip_checked_signal.emit(real_ip)
        except Exception:
            logger.warning("[ HOST_IP ] IP detection failed")

        completed = 0
        max_workers = min(self.settings.get('threads', 50), 100)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for i, proxy in enumerate(self.proxies):
                if not self._is_running:
                    break
                future = executor.submit(self.check_single_proxy, proxy, i)
                futures[future] = i

            for future in concurrent.futures.as_completed(futures):
                if not self._is_running:
                    break

                idx = futures[future]
                try:
                    result = future.result(timeout=2)
                    self.proxies[idx].update(result)
                    self.proxy_checked.emit(idx, result)
                except Exception as e:
                    logger.error(f"[ CHECK_ERR ] #{idx}: {e}")

                completed += 1
                pct = int((completed / total) * 100)
                self.progress.emit(pct, f"Checked {completed}/{total}")

        alive = sum(1 for p in self.proxies if p.get('status') == 'alive')
        slow = sum(1 for p in self.proxies if p.get('status') == 'slow')
        dead = sum(1 for p in self.proxies if p.get('status') == 'dead')

        logger.info(f"[ CHECKER_DONE ] {alive} alive | {slow} slow | {dead} dead")


# ============================================================================
# Main Application (Graphical Interface Engine)
# ============================================================================
class ProxySwitcherPro(QMainWindow):
    def __init__(self):
        super().__init__()

        logger.info("=" * 70)
        logger.info(f"Initializing {APP_NAME} v{VERSION}")
        logger.info("=" * 70)

        self.proxies = []
        self.active_proxy = None
        self.proxy_enabled = False
        self.settings = self.default_settings()
        self.checker_thread = None
        self.grabber_thread = None

        try:
            self.load_settings()
            self.init_ui()
            self.apply_theme()
            logger.info("UI initialized successfully")
            self.load_proxies()
            logger.info(f"Loaded {len(self.proxies)} proxies")
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            raise

        self.ip_timer = QTimer()
        self.ip_timer.timeout.connect(self.update_my_ip)
        self.ip_timer.start(15000)

        self.rotate_timer = QTimer()
        self.rotate_timer.timeout.connect(self.rotate_proxy)
        self.rotate_timer_interval = 60

        QTimer.singleShot(1000, self.update_my_ip)
        logger.info("Application ready")
        logger.info("=" * 70)

    def default_settings(self):
        return {
            'theme': 'dark',
            'timeout': 10,
            'threads': 30,
            'auto_rotate': False,
            'last_proxy': None
        }

    def init_ui(self):
        """Initialize the UI with professional design"""
        self.setWindowTitle(f"Proxy Switcher Pro v{VERSION}")
        self.setGeometry(100, 100, 1200, 700)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Top bar with title and IP label
        top_layout = QHBoxLayout()
        title = QLabel(f"Proxy Switcher Pro - v{VERSION}")
        title.setObjectName("title")
        top_layout.addWidget(title)
        top_layout.addStretch()

        self.ip_label = QLabel("IP: Scanning...")
        self.ip_label.setObjectName("subtitle")
        top_layout.addWidget(self.ip_label)

        self.status_btn = QPushButton("OFFLINE")
        self.status_btn.setMaximumWidth(160)
        self.status_btn.clicked.connect(self.toggle_proxy)
        top_layout.addWidget(self.status_btn)

        layout.addLayout(top_layout)

        # Control buttons
        btn_layout = QHBoxLayout()
        buttons = [
            ("Grab Proxies", self.grab_proxies),
            ("Verify All", self.check_all_proxies),
            ("Delete Dead", self.delete_dead_proxies),
            ("Delete Slow", self.delete_slow_proxies),
            ("Import", self.import_proxies),
            ("Auto Rotate", self.setup_auto_rotate),
            ("Clear All", self.clear_all),
        ]

        for text, callback in buttons:
            btn = QPushButton(text)
            btn.setMinimumWidth(100)
            btn.clicked.connect(callback)
            btn_layout.addWidget(btn)

        layout.addLayout(btn_layout)

        # Proxy table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "#", "IP", "PORT", "TYPE", "STATUS", "SPEED", "ANONYMITY", "COUNTRY"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.setup_table_context_menu()
        layout.addWidget(self.table)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(25)
        layout.addWidget(self.progress_bar)

        # Statistics bar
        self.stats_label = QLabel("Total: 0 | Alive: 0 | Slow: 0 | Dead: 0")
        self.stats_label.setObjectName("stats")
        layout.addWidget(self.stats_label)

    def apply_theme(self):
        """Apply black & white professional theme"""
        self.setStyleSheet(Theme.stylesheet())

    def load_proxies(self):
        """[ LOAD_PROXIES ] Loads proxy nodes from storage"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, encoding='utf-8') as f:
                    self.proxies = json.load(f)
                logger.info(f"[ LOADED ] {len(self.proxies)} proxy nodes from {CONFIG_FILE}")
            self.refresh_table()
        except Exception as e:
            logger.error(f"[ LOAD_ERR ] {e}")

    def save_proxies(self):
        """[ DISK_SYNC ] Saves proxy nodes to disk with guaranteed sync"""
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.proxies, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())

            logger.info(f"[ SYNCED ] Proxy nodes written: {CONFIG_FILE} ({len(self.proxies)} objects)")
        except Exception as e:
            logger.error(f"[ FAILED ] Error syncing proxy nodes: {e}")

    def load_settings(self):
        """[ LOAD_SETTINGS ] Loads application configuration"""
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, encoding='utf-8') as f:
                    self.settings.update(json.load(f))
                logger.info("[ LOADED ] Application configuration loaded")
        except Exception as e:
            logger.error(f"[ LOAD_ERR ] {e}")

    def save_settings(self):
        """[ CONFIG_STORE ] Saves user configuration parameters"""
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
                f.flush()
                os.fsync(f.fileno())

            logger.info(f"[ SYNCED ] Settings written: {SETTINGS_FILE}")
        except Exception as e:
            logger.error(f"[ FAILED ] Error syncing config: {e}")

    def refresh_table(self):
        self.table.setRowCount(len(self.proxies))
        for row, proxy in enumerate(self.proxies):
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))

            ip_item = QTableWidgetItem(proxy.get('ip', ''))
            status = proxy.get('status', 'unknown')
            if status == 'alive':
                ip_item.setForeground(QColor(Theme.SUCCESS))
            elif status == 'dead':
                ip_item.setForeground(QColor(Theme.ERROR))
            elif status == 'slow':
                ip_item.setForeground(QColor(Theme.WARNING))
            self.table.setItem(row, 1, ip_item)

            self.table.setItem(row, 2, QTableWidgetItem(str(proxy.get('port', ''))))

            # Proxy type
            proxy_type = proxy.get('type', 'HTTP')
            type_emoji = '🔗' if proxy_type == 'HTTP' else '🔒' if proxy_type == 'HTTPS' else '🌐'
            if 'SOCKS5' in proxy_type:
                type_emoji = '🔐'
            elif 'SOCKS4' in proxy_type:
                type_emoji = '🔒'
            type_item = QTableWidgetItem(f"{type_emoji} {proxy_type}")
            type_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, type_item)

            status_item = QTableWidgetItem(status.upper())
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            if status == 'alive':
                status_item.setBackground(QColor(Theme.SUCCESS))
                status_item.setForeground(QColor('#ffffff'))
            elif status == 'dead':
                status_item.setBackground(QColor(Theme.ERROR))
                status_item.setForeground(QColor('#ffffff'))
            elif status == 'slow':
                status_item.setBackground(QColor(Theme.WARNING))
                status_item.setForeground(QColor('#ffffff'))
            elif status == 'fresh':
                status_item.setBackground(QColor(Theme.FG_DARK))
                status_item.setForeground(QColor('#ffffff'))
            self.table.setItem(row, 4, status_item)

            speed = proxy.get('speed', '')
            speed_str = f"{speed}s" if speed else "-"
            speed_item = QTableWidgetItem(speed_str)
            speed_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, speed_item)

            # Anonymity
            anonymity = proxy.get('anonymity', 'unknown')
            anonymity_emoji = '🟢' if anonymity == 'elite' else '🟡' if anonymity == 'anonymous' else '🔴'
            anonymity_item = QTableWidgetItem(f"{anonymity_emoji} {anonymity}")
            anonymity_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 6, anonymity_item)

            # Country
            country = proxy.get('country', '🌍')
            country_item = QTableWidgetItem(str(country))
            country_item.setTextAlignment(Qt.AlignCenter)

            # Favorite - star before country
            is_favorite = proxy.get('favorite', False)
            if is_favorite:
                country_item.setText(f"⭐ {country}")
                country_item.setForeground(QColor('#FFD700'))

            self.table.setItem(row, 7, country_item)

        self._update_stats()

    def _update_stats(self):
        total = len(self.proxies)
        alive = sum(1 for p in self.proxies if p.get('status') == 'alive')
        slow = sum(1 for p in self.proxies if p.get('status') == 'slow')
        dead = sum(1 for p in self.proxies if p.get('status') == 'dead')
        self.stats_label.setText(f"Total: {total} | Alive: {alive} | Slow: {slow} | Dead: {dead}")

    def grab_proxies(self):
        # Dialog for choosing proxy count
        dialog = QDialog(self)
        dialog.setWindowTitle("Proxy Collection Settings")
        dialog.setStyleSheet(Theme.stylesheet())
        layout = QVBoxLayout(dialog)

        # Title
        title = QLabel("How many proxies to collect?")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)

        # Description
        desc = QLabel("Enter the number of proxies (50-500):\nMore = longer collection time")
        desc.setFont(QFont("Segoe UI", 10))
        desc.setStyleSheet(f"color: {Theme.FG_DIM};")
        layout.addWidget(desc)

        # Spinner
        spinbox = QSpinBox()
        spinbox.setRange(10, 500)
        spinbox.setValue(100)
        spinbox.setSingleStep(10)
        spinbox.setFont(QFont("Segoe UI", 12, QFont.Bold))
        spinbox.setMinimumHeight(40)
        layout.addWidget(spinbox)

        # Checkbox to add to existing
        add_checkbox = QCheckBox(f"Add to existing ({len(self.proxies)} proxies)")
        add_checkbox.setFont(QFont("Segoe UI", 10))
        add_checkbox.setChecked(len(self.proxies) > 0)
        layout.addWidget(add_checkbox)

        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("COLLECT")
        ok_btn.setObjectName("primary")
        cancel_btn = QPushButton("CANCEL")
        ok_btn.setMinimumHeight(36)
        cancel_btn.setMinimumHeight(36)
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # Show dialog
        if dialog.exec_() != QDialog.Accepted:
            return

        count = spinbox.value()
        add_to_existing = add_checkbox.isChecked()

        # Request confirmation
        action = "add" if add_to_existing else "collect"
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Will {action} {count} proxies?\n\nThis may take 2-5 minutes...",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        if not add_to_existing:
            self.proxies = []

        self.refresh_table()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.grabber_thread = ProxyGrabber(max_proxies=count)
        self.grabber_thread.finished.connect(self.on_grab_finished)
        self.grabber_thread.progress.connect(lambda p, m: self.progress_bar.setValue(p))
        self.grabber_thread.start()
        logger.info(f"Started collection of {count} proxies (add: {add_to_existing})...")

    def on_grab_finished(self, proxies):
        """[ GRAB_COMPLETE ] Handles completed proxy collection"""
        # Merge new nodes with existing database
        self.proxies.extend(proxies)

        # Deduplicate by IP:PORT
        seen = set()
        unique = []
        for p in self.proxies:
            key = f"{p.get('ip')}:{p.get('port')}"
            if key not in seen:
                seen.add(key)
                unique.append(p)
        self.proxies = unique

        self.refresh_table()
        self.progress_bar.setVisible(False)
        self.save_proxies()

        total = len(self.proxies)
        if total > 0:
            logger.info(f"[ AGGREGATED ] {total} unique proxy nodes")
            QMessageBox.information(
                self,
                "Collection Complete",
                f"Total proxies: {total}\n\n"
                f"Saved to: {CONFIG_FILE}\n\n"
                f"Now click 'Verify All' to check them!"
            )
        else:
            logger.warning("[ GRAB_FAILED ] Collection completed with 0 nodes")
            QMessageBox.warning(
                self,
                "Collection Failed",
                "Failed to collect proxies\n\n"
                "Try again later or check network connection"
            )

    def check_all_proxies(self):
        if not self.proxies:
            QMessageBox.warning(self, "Error", "No proxies to check")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.checker_thread = ProxyChecker(self.proxies, self.settings)
        self.checker_thread.progress.connect(lambda p, m: self.progress_bar.setValue(p))
        self.checker_thread.ip_checked_signal.connect(lambda ip: self.ip_label.setText(f"IP: {ip}"))
        self.checker_thread.proxy_checked.connect(self.on_proxy_checked)
        self.checker_thread.finished.connect(self.on_check_finished)
        self.checker_thread.start()

    def on_proxy_checked(self, index, result):
        if index < self.table.rowCount():
            QTimer.singleShot(0, lambda: self._update_table_row(index, result))

    def _update_table_row(self, index, result):
        """[ REALTIME_UPDATE ] Updates table row with proxy check result"""
        try:
            if index >= self.table.rowCount() or index >= len(self.proxies):
                return

            status = result.get('status', 'unknown')
            status_item = QTableWidgetItem(status.upper())
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setFont(QFont("Segoe UI", 10, QFont.Bold))

            if status == 'alive':
                status_item.setForeground(QColor('#ffffff'))
                status_item.setBackground(QColor(Theme.SUCCESS))
            elif status == 'dead':
                status_item.setForeground(QColor('#ffffff'))
                status_item.setBackground(QColor(Theme.ERROR))
            elif status == 'slow':
                status_item.setForeground(QColor('#ffffff'))
                status_item.setBackground(QColor(Theme.WARNING))

            self.table.setItem(index, 4, status_item)

            speed = result.get('speed', '')
            speed_item = QTableWidgetItem(f"{speed}s" if speed else "-")
            self.table.setItem(index, 5, speed_item)

            country = result.get('country', '🌍')
            country_item = QTableWidgetItem(str(country))
            country_item.setTextAlignment(Qt.AlignCenter)

            # If proxy is favorite, add star
            if self.proxies[index].get('favorite', False):
                country_item.setText(f"⭐ {country}")
                country_item.setForeground(QColor('#FFD700'))

            self.table.setItem(index, 7, country_item)

            # Update data in list EXCLUDING user flags
            self.proxies[index]['status'] = status
            self.proxies[index]['speed'] = speed
            self.proxies[index]['country'] = country
            self.proxies[index]['anonymity'] = result.get('anonymity', 'unknown')

            # Immediate disk sync
            self.save_proxies()
            logger.debug(f"[ NODE_UPDATED ] #{index + 1}: {status} ({speed}s)")
        except Exception as e:
            logger.error(f"[ UPDATE_ERR ] {e}")

    def on_check_finished(self, proxies):
        """[ CHECK_COMPLETE ] Handles completed proxy verification"""
        # Integrate check results WITHOUT full database replacement
        for i, result in enumerate(proxies):
            if i < len(self.proxies):
                self.proxies[i]['status'] = result.get('status', 'unknown')
                self.proxies[i]['speed'] = result.get('speed', '')
                self.proxies[i]['country'] = result.get('country', '🌍')
                self.proxies[i]['anonymity'] = result.get('anonymity', 'unknown')

        self.refresh_table()
        self.progress_bar.setVisible(False)
        self.save_proxies()  # Final sync ONCE

        alive = sum(1 for p in self.proxies if p.get('status') == 'alive')
        dead = sum(1 for p in self.proxies if p.get('status') == 'dead')

        self.status_btn.setText(f"VERIFIED: {alive} alive | {dead} dead")
        logger.info(f"[ VERIFICATION_COMPLETE ] {alive} alive out of {len(self.proxies)} nodes")

    def delete_dead_proxies(self):
        dead = [p for p in self.proxies if p.get('status') == 'dead']
        if not dead:
            QMessageBox.information(self, "Info", "No dead proxies")
            return

        reply = QMessageBox.question(self, "Confirmation", f"Delete {len(dead)} dead proxies?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.proxies = [p for p in self.proxies if p.get('status') != 'dead']
            self.refresh_table()
            self.save_proxies()
            logger.info(f"Deleted {len(dead)} dead proxies")

    def delete_slow_proxies(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Delete Slow Proxies")
        dialog.setStyleSheet(Theme.stylesheet())
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Delete proxies slower than (sec):"))
        speed_spin = QDoubleSpinBox()
        speed_spin.setRange(0.1, 60.0)
        speed_spin.setValue(2.0)
        layout.addWidget(speed_spin)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("Delete")
        ok_btn.setObjectName("danger")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        if dialog.exec_() != QDialog.Accepted:
            return

        threshold = speed_spin.value()
        slow = [p for p in self.proxies if p.get('speed', 0) and float(p.get('speed', 0)) > threshold]

        if not slow:
            QMessageBox.information(self, "Info", f"No proxies slower than {threshold}s")
            return

        reply = QMessageBox.question(self, "Confirmation", f"Delete {len(slow)} slow proxies?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.proxies = [p for p in self.proxies if not (p.get('speed', 0) and float(p.get('speed', 0)) > threshold)]
            self.refresh_table()
            self.save_proxies()
            logger.info(f"Deleted {len(slow)} slow proxies")

    def import_proxies(self):
        text, ok = QInputDialog.getMultiLineText(self, "Import Proxies", "Enter proxies (IP:PORT):")
        if not ok or not text.strip():
            return

        pattern = r'(\d+\.\d+\.\d+\.\d+):(\d+)'
        matches = re.findall(pattern, text)

        added = 0
        for ip, port in matches:
            self.proxies.append({'ip': ip, 'port': port, 'type': 'HTTP', 'status': 'fresh', 'speed': '', 'anonymity': 'unknown', 'country': 'unknown'})
            added += 1

        self.refresh_table()
        self.save_proxies()
        QMessageBox.information(self, "Success", f"Imported {added} proxies")
        logger.info(f"Imported {added} proxies")

    def clear_all(self):
        reply = QMessageBox.question(self, "Confirmation", "Clear ALL proxies?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.proxies = []
            self.refresh_table()
            self.save_proxies()
            logger.info("All proxies deleted")

    def toggle_proxy(self):
        """Toggles proxy on/off"""
        if self.proxy_enabled:
            self.disable_proxy()
        else:
            self.enable_proxy()

    def enable_proxy(self):
        """Enables selected proxy"""
        if not IS_WINDOWS:
            QMessageBox.warning(self, "Error", "System proxy configuration is only supported on Windows")
            return

        row = self.table.currentRow()
        if row < 0 or row >= len(self.proxies):
            QMessageBox.warning(self, "Error", "Select a proxy from the table")
            return

        proxy = self.proxies[row]
        # Allow enabling ALIVE and SLOW proxies
        if proxy.get('status') not in ['alive', 'slow']:
            QMessageBox.warning(self, "Error", f"Only working proxies can be activated (ALIVE or SLOW)\nCurrent: {proxy.get('status').upper()}")
            return

        try:
            import winreg
            import ctypes
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"{proxy['ip']}:{proxy['port']}")
            winreg.CloseKey(key)
            ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)

            self.proxy_enabled = True
            self.active_proxy = row
            self.settings['last_proxy'] = row
            self.save_settings()
            status_emoji = "🟢" if proxy.get('status') == 'alive' else "🟡"
            speed_info = f" ({proxy.get('speed', '?')}s)" if proxy.get('speed') else ""
            self.status_btn.setText(f"{status_emoji} ENABLED: {proxy['ip']}:{proxy['port']}{speed_info}")
            self.status_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.SUCCESS};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #388e3c;
                }}
            """)
            logger.info(f"Proxy enabled: {proxy['ip']}:{proxy['port']} ({proxy.get('status')}){speed_info}")
            QMessageBox.information(self, "Success", f"Proxy enabled\n{proxy['ip']}:{proxy['port']}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to enable proxy: {e}")
            logger.error(f"Error: {e}")

    def disable_proxy(self):
        """Disables proxy in Windows"""
        if not IS_WINDOWS:
            QMessageBox.warning(self, "Error", "System proxy configuration is only supported on Windows")
            return

        try:
            import winreg
            import ctypes
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)

            self.proxy_enabled = False
            self.active_proxy = None
            self.save_settings()
            self.status_btn.setText("PROXY DISABLED")
            self.status_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.ERROR};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #d32f2f;
                }}
            """)
            logger.info("Proxy disabled")
            QMessageBox.information(self, "Success", "Proxy disabled\nBack to direct connection")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to disable proxy: {e}")
            logger.error(f"Error disabling: {e}")

    def rotate_proxy(self):
        """Automatically switches to next alive proxy"""
        if not self.proxy_enabled:
            logger.info("Auto-rotation: proxy not enabled, skipping")
            return

        alive_proxies = [i for i, p in enumerate(self.proxies) if p.get('status') == 'alive']

        if not alive_proxies:
            logger.warning("No alive proxies for rotation")
            return

        # Select random alive proxy
        next_idx = random.choice(alive_proxies)
        self.table.setCurrentCell(next_idx, 0)
        self.toggle_proxy()
        logger.info(f"Rotation: selected proxy #{next_idx + 1}")

    def setup_auto_rotate(self):
        """Opens auto-rotation settings dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Auto-Rotation Settings")
        dialog.setStyleSheet(Theme.stylesheet())
        layout = QVBoxLayout(dialog)

        # Title
        title = QLabel("Automatic proxy rotation")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)

        # Enable auto-rotation
        enable_checkbox = QCheckBox("Enable auto-rotation")
        enable_checkbox.setFont(QFont("Segoe UI", 11))
        enable_checkbox.setChecked(self.settings.get('auto_rotate', False))
        layout.addWidget(enable_checkbox)

        # Interval
        layout.addWidget(QLabel("Interval (seconds):"))
        interval_spin = QSpinBox()
        interval_spin.setRange(5, 3600)
        interval_spin.setValue(self.rotate_timer_interval)
        interval_spin.setSingleStep(5)
        interval_spin.setMinimumHeight(36)
        layout.addWidget(interval_spin)

        layout.addSpacing(15)
        layout.addWidget(QLabel("Tip: Use auto-rotation to change proxy every N seconds"))

        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("SAVE")
        ok_btn.setObjectName("primary")
        cancel_btn = QPushButton("CANCEL")
        ok_btn.setMinimumHeight(36)
        cancel_btn.setMinimumHeight(36)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        def save_settings():
            enabled = enable_checkbox.isChecked()
            interval = interval_spin.value()

            self.settings['auto_rotate'] = enabled
            self.rotate_timer_interval = interval
            self.save_settings()

            if enabled:
                self.rotate_timer.start(interval * 1000)
                QMessageBox.information(
                    self,
                    "Auto-rotation enabled",
                    f"Proxy will change every {interval} sec"
                )
                logger.info(f"Auto-rotation enabled: interval {interval} sec")
            else:
                self.rotate_timer.stop()
                QMessageBox.information(
                    self,
                    "Auto-rotation disabled",
                    "Auto-rotation disabled"
                )
                logger.info("Auto-rotation disabled")

            dialog.accept()

        ok_btn.clicked.connect(save_settings)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec_()

    def update_my_ip(self):
        def check_ip():
            try:
                response = requests.get('https://api.ipify.org?format=json', timeout=3)
                ip = response.json().get('ip', 'Unknown')
                QTimer.singleShot(0, lambda: self.ip_label.setText(f"IP: {ip}"))
            except Exception:
                QTimer.singleShot(0, lambda: self.ip_label.setText("IP: Unknown"))

        threading.Thread(target=check_ip, daemon=True).start()

    def closeEvent(self, event):
        """[ SHUTDOWN ] Saves state and data on application exit"""
        logger.info("=" * 70)
        logger.info("[ SHUTDOWN ] Initiating final data save...")
        logger.info("=" * 70)

        try:
            logger.info(f"[ AUDIT ] Nodes in memory: {len(self.proxies)}")

            # Validate and clean invalid records
            before = len(self.proxies)
            cleaned = [p for p in self.proxies if p.get('ip') and p.get('port')]
            logger.info(f"[ CLEANUP ] Removed {before - len(cleaned)} invalid records")
            self.proxies = cleaned

            # Sync proxy database
            logger.info(f"[ SYNC ] Saving {len(self.proxies)} nodes to disk...")
            self.save_proxies()

            # Sync configuration
            logger.info("[ SYNC ] Saving configuration parameters...")
            self.save_settings()

            # Verify file integrity
            if CONFIG_FILE.exists():
                size = CONFIG_FILE.stat().st_size
                logger.info(f"[ VERIFIED ] proxies.json: {size} bytes")
            else:
                logger.error("[ CRITICAL ] proxies.json not found!")

            if SETTINGS_FILE.exists():
                size = SETTINGS_FILE.stat().st_size
                logger.info(f"[ VERIFIED ] settings.json: {size} bytes")
            else:
                logger.error("[ CRITICAL ] settings.json not found!")

            logger.info("=" * 70)
            logger.info("[ SHUTDOWN ] Application closed. Data saved successfully.")
            logger.info("=" * 70)
        except Exception as e:
            logger.error(f"[ FATAL ] Critical error on exit: {e}")
            import traceback
            logger.error(f"[ STACK ] {traceback.format_exc()}")

        event.accept()

    def setup_table_context_menu(self):
        """Adds context menu for the table"""
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_table_context_menu)

    def show_table_context_menu(self, pos):
        """Shows context menu on right-click"""
        index = self.table.rowAt(pos.y())
        if index < 0 or index >= len(self.proxies):
            return

        menu = QMenu(self)
        proxy = self.proxies[index]
        is_favorite = proxy.get('favorite', False)

        # Favorite menu item
        if is_favorite:
            action = menu.addAction("★ Remove from favorites")
        else:
            action = menu.addAction("☆ Add to favorites")

        action.triggered.connect(lambda: self.toggle_favorite(index))

        # More useful items
        menu.addSeparator()

        copy_action = menu.addAction("📋 Copy IP:Port")
        copy_action.triggered.connect(lambda: self.copy_proxy_to_clipboard(index))

        menu.exec_(self.table.mapToGlobal(pos))

    def toggle_favorite(self, index):
        """[ FAVORITE ] Adds/removes proxy node to favorites"""
        if index < 0 or index >= len(self.proxies):
            return

        self.proxies[index]['favorite'] = not self.proxies[index].get('favorite', False)
        self.save_proxies()  # Immediate sync
        self.refresh_table()

        is_favorite = self.proxies[index]['favorite']
        status = "added to" if is_favorite else "removed from"
        logger.info(f"[ FAVORITE ] Node #{index + 1} {status} favorites")

    def copy_proxy_to_clipboard(self, index):
        """[ CLIPBOARD ] Copies proxy node address to clipboard"""
        if index < 0 or index >= len(self.proxies):
            return

        proxy = self.proxies[index]
        proxy_str = f"{proxy['ip']}:{proxy['port']}"

        clipboard = QApplication.clipboard()
        clipboard.setText(proxy_str)

        logger.info(f"[ COPIED ] {proxy_str} copied to clipboard")
        QMessageBox.information(self, "Success", f"Copied to clipboard:\n{proxy_str}")


# ============================================================================
# Application Launcher
# ============================================================================
def main():
    logger.info("[ LAUNCH ] Initializing Qt application...")
    app = QApplication(sys.argv)
    logger.info("[ QT_READY ] Qt ready")

    # Show splash screen
    splash = SplashScreen()
    splash.show()

    def create_main_window():
        window = ProxySwitcherPro()
        window.show()
        logger.info("[ WINDOW_SHOWN ] Application displayed on screen")
        return window

    splash.finished.connect(create_main_window)
    logger.info("[ RUNNING ] Entering event loop...")

    sys.exit(app.exec_())


if __name__ == "__main__":
    logger.info("\n" + "=" * 70)
    logger.info("[ PROXY_SWITCHER_PROFESSIONAL_v2.0.0 ]")
    logger.info("=" * 70)
    main()
    logger.info("=" * 70)
    logger.info("[ PROGRAM_TERMINATED ] Shutting down")
    logger.info("=" * 70)


