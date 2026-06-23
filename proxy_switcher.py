#!/usr/bin/env python3
"""
Proxy Switcher Pro - Professional Proxy Management Tool
Version 1.0.0

Features:
- Multi-source proxy aggregation
- Async proxy validation and verification
- System-level proxy configuration
- Real-time proxy monitoring and metrics
"""
import sys
import os
import json
import socket
import threading
import time
import re
import random
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
    except Exception as e:
        pass

logger.info("=" * 70)
logger.info("Proxy Switcher Pro v1.0.0 - Starting Application")
logger.info("Loading modules: requests, BeautifulSoup, PyQt5...")
logger.info("=" * 70)

# ============================================================================
# Application Configuration
# ============================================================================
APP_NAME = "Proxy Switcher Pro"
VERSION = "1.0.0"
CONFIG_DIR = Path.home() / "Documents" / "ProxySwitcher"
CONFIG_FILE = CONFIG_DIR / "proxies.json"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

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

class SplashScreen(QWidget):
    finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        screen = QApplication.primaryScreen()
        self.setGeometry(screen.geometry())
        
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        title = QLabel("Proxy Switcher Pro")
        title.setFont(QFont("Arial", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333333;")
        layout.addWidget(title)
        
        version = QLabel("v1.0.0")
        version.setFont(QFont("Arial", 14))
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("color: #666666;")
        layout.addWidget(version)
        
        layout.addSpacing(20)
        
        self.status = QLabel("Initializing...")
        self.status.setFont(QFont("Arial", 12))
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("color: #555555;")
        layout.addWidget(self.status)
        
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(400)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 3px;
                background: #f0f0f0;
            }
            QProgressBar::chunk {
                background: #0078d4;
                border-radius: 2px;
            }
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
        logger.info(f"[ ⚡ GRABBER ] Инициализирован (max_nodes={max_proxies})")
        
    def stop(self):
        self._is_running = False
        logger.info("[ ⊘ GRABBER ] Процесс остановлен")
        
    def fetch_url(self, url, timeout=10) -> Optional[str]:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            logger.debug(f"[ ✓ FETCH ] {url}")
            return response.text
        except requests.exceptions.Timeout:
            logger.warning(f"[ ⏱ TIMEOUT ] {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning(f"[ ✗ CONN_ERR ] {url}")
            return None
        except Exception as e:
            logger.error(f"[ ✗ FETCH_ERR ] {url}: {e}")
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
                except:
                    continue
            logger.info(f"[ ✓ PARSE_TABLE ] {len(proxies)} прокси из таблицы")
            return proxies
        except Exception as e:
            logger.error(f"[ ✗ PARSE_ERR ] {e}")
            return []
            
    def is_valid_ip(self, ip: str) -> bool:
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            return all(0 <= int(part) <= 255 for part in parts)
        except:
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
                except:
                    continue
            logger.info(f"[ ✓ PARSE_TEXT ] {len(proxies)} прокси из текста")
            return proxies
        except Exception as e:
            logger.error(f"[ ✗ PARSE_ERR ] {e}")
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
            logger.debug(f"[ ✓ NODE_ADD ] {ip}:{port} ({proxy_type})")
            
    def run(self):
        logger.info(f"[ ▶ GRABBER ] Запуск сбора из {len(PROXY_SOURCES)} источников")
        total_sources = len(PROXY_SOURCES)
        
        for i, url in enumerate(PROXY_SOURCES):
            if not self._is_running or len(self.found_proxies) >= self.max_proxies:
                break
            progress = int((i / total_sources) * 100)
            msg = f"Сбор... {len(self.found_proxies)}/{self.max_proxies}"
            self.progress.emit(progress, msg)
            
            # Определяем тип прокси по URL
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
                logger.error(f"[ ✗ SOURCE_ERR ] {url}: {e}")
                continue
                
        logger.info(f"[ ✓ GRABBER_DONE ] Собрано {len(self.found_proxies)} прокси-нодов")
        self.progress.emit(100, f"Готово: {len(self.found_proxies)} прокси")
        self.finished.emit(self.found_proxies)


# ============================================================================
# ⚡ ПРОКСИ-ВЕРИФИКАТОР (Advanced Node Validation System)
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
        logger.info(f"[ ⚡ CHECKER ] Инициализирован для {len(proxies)} нодов")
        
    def stop(self):
        self._is_running = False
        logger.info("[ ⊘ CHECKER ] Процесс верификации остановлен")
    
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
        except:
            return results
        
        # Проверка HTTP/HTTPS прокси
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
                    except:
                        results['anonymity'] = 'anonymous'
                elif response.status_code in [407, 408, 429]:
                    results['status'] = 'slow'
                    results['speed'] = round(response_time, 2)
                    results['error'] = f'HTTP {response.status_code}'
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
        
        # Для SOCKS прокси проверяем только доступность
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
            except:
                results['status'] = 'dead'
        
        # Определение страны - лучший сервис с множеством попыток
        country = self._get_country_by_ip(ip)
        results['country'] = country
        
        return results
    
    def _get_country_by_ip(self, ip: str) -> str:
        """[ GEO ] Определяет страну по IP используя несколько источников"""
        # Попытка 1: ip-api.com
        try:
            response = requests.get(f'http://ip-api.com/json/{ip}', timeout=1)
            if response.status_code == 200:
                country = response.json().get('country')
                if country:
                    return country[:2]  # Возвращаем ISO код страны
        except:
            pass
        
        # Попытка 2: ipapi.co
        try:
            response = requests.get(f'https://ipapi.co/{ip}/json/', timeout=1)
            if response.status_code == 200:
                country = response.json().get('country_code')
                if country:
                    return country
        except:
            pass
        
        # Попытка 3: ipstack (если доступен)
        try:
            response = requests.get(f'http://geoip.vbb.app/{ip}', timeout=1)
            if response.status_code == 200:
                country = response.json().get('country_code')
                if country:
                    return country
        except:
            pass
        
        return '🌍'  # Дефолт если не удалось определить
        
    def run(self):
        total = len(self.proxies)
        logger.info(f"[ 🚀 CHECKER ] Запуск верификации {total} нодов (ThreadPool)")
        
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=2)
            real_ip = response.json().get('ip', 'Unknown')
            logger.info(f"[ 🌐 HOST_IP ] {real_ip}")
            self.ip_checked_signal.emit(real_ip)
        except:
            logger.warning("[ ⚠ HOST_IP ] Определение IP не удалось")
        
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
                    logger.error(f"[ ✗ CHECK_ERR ] #{idx}: {e}")
                
                completed += 1
                pct = int((completed / total) * 100)
                self.progress.emit(pct, f"⚡ Проверено {completed}/{total}")
        
        alive = sum(1 for p in self.proxies if p.get('status') == 'alive')
        slow = sum(1 for p in self.proxies if p.get('status') == 'slow')
        dead = sum(1 for p in self.proxies if p.get('status') == 'dead')
        
        logger.info(f"[ ✅ CHECKER_DONE ] ✅ {alive} живых | 🐢 {slow} медленных | ❌ {dead} мертвых")


# ============================================================================
# 🖥️ ГЛАВНОЕ ПРИЛОЖЕНИЕ (Graphical Interface Engine)
# ============================================================================
class ProxySwitcherPro(QMainWindow):
    def __init__(self):
        super().__init__()
        
        logger.info("=" * 70)
        logger.info(f"Initializing {APP_NAME} v{VERSION}")
        logger.info("=" * 70)
        
        self.proxies = []
        self.active_proxy = None
        self.proxy_enabled = False  # Флаг включен ли прокси
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
        title.setFont(QFont("Arial", 14, QFont.Bold))
        top_layout.addWidget(title)
        top_layout.addStretch()
        
        self.ip_label = QLabel("IP: Scanning...")
        self.ip_label.setFont(QFont("Arial", 10))
        top_layout.addWidget(self.ip_label)
        
        self.status_btn = QPushButton("OFFLINE")
        self.status_btn.setMaximumWidth(120)
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
        self.stats_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.stats_label)

    def apply_theme(self):
        """Apply professional light theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QLabel {
                color: #333333;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f5f5f5;
                gridline-color: #ddd;
                border: 1px solid #ddd;
            }
            QTableWidget::item {
                padding: 4px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                color: #333333;
                padding: 6px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: #f0f0f0;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 2px;
            }
            QScrollBar:vertical {
                width: 12px;
                background-color: #f0f0f0;
            }
            QScrollBar::handle:vertical {
                background-color: #0078d4;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #106ebe;
            }
        """)

    
    def load_proxies(self):
        """[ 📂 LOAD_PROXIES ] Загружает список прокси-нодов из хранилища"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE) as f:
                    self.proxies = json.load(f)
                logger.info(f"[ ✓ LOADED ] {len(self.proxies)} прокси-нодов из {CONFIG_FILE}")
            self.refresh_table()
        except Exception as e:
            logger.error(f"[ ✗ LOAD_ERR ] {e}")
    
    def save_proxies(self):
        """[ ⚡ DISK_SYNC ] Сохраняет прокси-ноды на диск с гарантированной синхронизацией"""
        try:
            # ► Создание директории в файловой системе
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # ► Запись JSON-блока в буфер с принудительной синхронизацией
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.proxies, f, indent=2, ensure_ascii=False)
                f.flush()  # Очистка буфера приложения
                os.fsync(f.fileno())  # ✓ FIX: Синхронизация ВНУТРИ контекста
            
            logger.info(f"[ ✓ SYNCED ] Прокси-ноды записаны: {CONFIG_FILE} ({len(self.proxies)} объектов)")
            logger.info(f"[ ✓ VERIFIED ] Файл существует: {CONFIG_FILE.exists()}")
        except Exception as e:
            logger.error(f"[ ✗ FAILED ] Ошибка синхронизации прокси-ноды: {e}")
            logger.error(f"[ PATH ] {CONFIG_FILE}")
            import traceback
            logger.error(f"[ STACK ] {traceback.format_exc()}")
    
    def load_settings(self):
        """[ ⚙️ LOAD_SETTINGS ] Загружает конфигурацию приложения"""
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE) as f:
                    self.settings.update(json.load(f))
                logger.info("[ ✓ LOADED ] Конфигурация приложения загружена")
        except Exception as e:
            logger.error(f"[ ✗ LOAD_ERR ] {e}")
    
    def save_settings(self):
        """[ ⚙️ CONFIG_STORE ] Сохраняет пользовательские параметры конфигурации"""
        try:
            # ► Инициализация директории конфигурации
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # ► Запись конфиг-файла с обязательной синхронизацией
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=2)
                f.flush()  # Очистка буфера ОС
                os.fsync(f.fileno())  # ✓ FIX: Синхронизация ВНУТРИ контекста
            
            logger.info(f"[ ✓ SYNCED ] Настройки записаны: {SETTINGS_FILE}")
            logger.info(f"[ ✓ VERIFIED ] Файл конфига существует: {SETTINGS_FILE.exists()}")
        except Exception as e:
            logger.error(f"[ ✗ FAILED ] Ошибка синхронизации конфига: {e}")
            import traceback
            logger.error(f"[ STACK ] {traceback.format_exc()}")
    
    def refresh_table(self):
        self.table.setRowCount(len(self.proxies))
        for row, proxy in enumerate(self.proxies):
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            
            ip_item = QTableWidgetItem(proxy.get('ip', ''))
            status = proxy.get('status', 'unknown')
            if status == 'alive':
                ip_item.setForeground(QColor('#3fb950'))
            elif status == 'dead':
                ip_item.setForeground(QColor('#da3633'))
            elif status == 'slow':
                ip_item.setForeground(QColor('#bf8700'))
            self.table.setItem(row, 1, ip_item)
            
            self.table.setItem(row, 2, QTableWidgetItem(str(proxy.get('port', ''))))
            
            # Тип прокси с иконкой
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
            status_item.setFont(QFont("Arial", 10, QFont.Bold))
            if status == 'alive':
                status_item.setBackground(QColor('#238636'))
                status_item.setForeground(QColor('#ffffff'))
            elif status == 'dead':
                status_item.setBackground(QColor('#da3633'))
                status_item.setForeground(QColor('#ffffff'))
            elif status == 'slow':
                status_item.setBackground(QColor('#bf8700'))
                status_item.setForeground(QColor('#ffffff'))
            elif status == 'fresh':
                status_item.setBackground(QColor('#6c757d'))
                status_item.setForeground(QColor('#ffffff'))
            self.table.setItem(row, 4, status_item)
            
            speed = proxy.get('speed', '')
            speed_str = f"{speed}s" if speed else "-"
            speed_item = QTableWidgetItem(speed_str)
            speed_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, speed_item)
            
            # Анонимность с иконкой
            anonymity = proxy.get('anonymity', 'unknown')
            anonymity_emoji = '🟢' if anonymity == 'elite' else '🟡' if anonymity == 'anonymous' else '🔴'
            anonymity_item = QTableWidgetItem(f"{anonymity_emoji} {anonymity}")
            anonymity_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 6, anonymity_item)
            
            # Страна
            country = proxy.get('country', '🌍')
            country_item = QTableWidgetItem(str(country))
            country_item.setTextAlignment(Qt.AlignCenter)
            
            # Избранное - звезда перед страной
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
        self.stats_label.setText(f"📊 Всего: {total} | ✅ Живые: {alive} | 🐢 Медленные: {slow} | ❌ Мертвые: {dead}")
    
    def grab_proxies(self):
        # Диалог выбора количества прокси
        dialog = QDialog(self)
        dialog.setWindowTitle("⚙ Настройки сборки прокси")
        dialog.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #333;
                font-size: 11px;
            }
            QSpinBox {
                background-color: white;
                color: #333;
                border: 2px solid #667eea;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QCheckBox {
                color: #333;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #764ba2, stop:1 #667eea);
            }
        """)
        layout = QVBoxLayout(dialog)
        
        # Заголовок
        title = QLabel("🌐 Сколько прокси собрать?")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setStyleSheet("color: #333; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Описание
        desc = QLabel("Введите количество прокси (50-500):\nБольше = дольше собирается")
        desc.setFont(QFont("Segoe UI", 10))
        desc.setStyleSheet("color: #666;")
        layout.addWidget(desc)
        
        # Спиннер
        spinbox = QSpinBox()
        spinbox.setRange(10, 500)
        spinbox.setValue(100)
        spinbox.setSingleStep(10)
        spinbox.setFont(QFont("Segoe UI", 12, QFont.Bold))
        spinbox.setMinimumHeight(40)
        layout.addWidget(spinbox)
        
        # Чекбокс добавить к существующим
        add_checkbox = QCheckBox(f"✓ Добавить к существующим ({len(self.proxies)} прокси)")
        add_checkbox.setFont(QFont("Segoe UI", 10))
        add_checkbox.setStyleSheet("color: #333; margin-top: 10px;")
        add_checkbox.setChecked(len(self.proxies) > 0)
        layout.addWidget(add_checkbox)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("✓ СОБРАТЬ")
        cancel_btn = QPushButton("✖ ОТМЕНА")
        ok_btn.setMinimumHeight(36)
        cancel_btn.setMinimumHeight(36)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e0e0e0, stop:1 #ccc);
                color: #333;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ccc, stop:1 #b0b0b0);
            }
        """)
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        # Показать диалог
        if dialog.exec_() != QDialog.Accepted:
            return
        
        count = spinbox.value()
        add_to_existing = add_checkbox.isChecked()
        
        # Запросить подтверждение
        action = "добавить" if add_to_existing else "собрать"
        reply = QMessageBox.question(
            self, 
            "⚡ Подтверждение", 
            f"Будет {action} {count} прокси?\n\nЭто может занять 2-5 минут...",
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
        logger.info(f"⚡ Начата сборка {count} прокси (добавить: {add_to_existing})...")
    
    def on_grab_finished(self, proxies):
        """[ ✓ GRAB_COMPLETE ] Обработка завершенной сборки прокси-нодов"""
        # ► Объединение новых нодов с существующими базой
        self.proxies.extend(proxies)
        
        # ► Дедупликация по IP:PORT (исключение дубликатов)
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
            logger.info(f"[ ✓ AGGREGATED ] {total} уникальных прокси-нодов")
            logger.info(f"[ 💾 STORED ] Данные сохранены: {CONFIG_FILE}")
            QMessageBox.information(
                self,
                "[ ✅ GRAB_SUCCESS ]",
                f"✓ Всего прокси: {total}\n\n"
                f"📍 Сохранено: {CONFIG_FILE}\n\n"
                f"Теперь нажми 'ПРОВЕРИТЬ ВСЕ' для верификации!"
            )
        else:
            logger.warning("[ ⚠ GRAB_FAILED ] Сборка завершена с 0 нодов")
            QMessageBox.warning(
                self,
                "[ ⚠ GRAB_FAILED ]",
                "Не удалось собрать прокси\n\n"
                "Попробуй позже или проверь сетевое подключение"
            )
    
    def check_all_proxies(self):
        if not self.proxies:
            QMessageBox.warning(self, "Ошибка", "Нет прокси для проверки")
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
        """[ ⚡ REALTIME_UPDATE ] Обновление строки таблицы с результатом проверки ноды"""
        try:
            if index >= self.table.rowCount() or index >= len(self.proxies):
                return
            
            status = result.get('status', 'unknown')
            status_item = QTableWidgetItem(status.upper())
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setFont(QFont("Arial", 10, QFont.Bold))
            
            if status == 'alive':
                status_item.setForeground(QColor('#ffffff'))
                status_item.setBackground(QColor('#238636'))
            elif status == 'dead':
                status_item.setForeground(QColor('#ffffff'))
                status_item.setBackground(QColor('#da3633'))
            elif status == 'slow':
                status_item.setForeground(QColor('#ffffff'))
                status_item.setBackground(QColor('#bf8700'))
            
            self.table.setItem(index, 4, status_item)
            
            speed = result.get('speed', '')
            speed_item = QTableWidgetItem(f"{speed}s" if speed else "-")
            self.table.setItem(index, 5, speed_item)
            
            country = result.get('country', '🌍')
            country_item = QTableWidgetItem(str(country))
            country_item.setTextAlignment(Qt.AlignCenter)
            
            # Если прокси избранное, добавим звезду
            if self.proxies[index].get('favorite', False):
                country_item.setText(f"⭐ {country}")
                country_item.setForeground(QColor('#FFD700'))
            
            self.table.setItem(index, 7, country_item)
            
            # ► Обновляем данные в списке ИСКЛЮЧАЯ пользовательские флаги
            self.proxies[index]['status'] = status
            self.proxies[index]['speed'] = speed
            self.proxies[index]['country'] = country
            self.proxies[index]['anonymity'] = result.get('anonymity', 'unknown')
            
            # ► Немедленная синхронизация с диском
            self.save_proxies()
            logger.debug(f"[ ✓ NODE_UPDATED ] #{index + 1}: {status} ({speed}s)")
        except Exception as e:
            logger.error(f"[ ✗ UPDATE_ERR ] {e}")
    
    def on_check_finished(self, proxies):
        """[ ✓ CHECK_COMPLETE ] Обработка завершенной верификации прокси-нодов"""
        # ► Интеграция результатов проверки БЕЗ полной замены базы
        for i, result in enumerate(proxies):
            if i < len(self.proxies):
                self.proxies[i]['status'] = result.get('status', 'unknown')
                self.proxies[i]['speed'] = result.get('speed', '')
                self.proxies[i]['country'] = result.get('country', '🌍')
                self.proxies[i]['anonymity'] = result.get('anonymity', 'unknown')
        
        self.refresh_table()
        self.progress_bar.setVisible(False)
        self.save_proxies()  # ► Финальная синхронизация ОДИН раз
        
        alive = sum(1 for p in self.proxies if p.get('status') == 'alive')
        dead = sum(1 for p in self.proxies if p.get('status') == 'dead')
        
        self.status_btn.setText(f"[ ✅ VERIFIED ] {alive} активных | ❌ {dead} неактивных")
        logger.info(f"[ ✓ VERIFICATION_COMPLETE ] ✅ {alive} активных из {len(self.proxies)} нодов")
    
    def delete_dead_proxies(self):
        dead = [p for p in self.proxies if p.get('status') == 'dead']
        if not dead:
            QMessageBox.information(self, "Информация", "Нет нерабочих прокси")
            return
        
        reply = QMessageBox.question(self, "Подтверждение", f"Удалить {len(dead)} нерабочих прокси?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.proxies = [p for p in self.proxies if p.get('status') != 'dead']
            self.refresh_table()
            self.save_proxies()
            logger.info(f"🗑 Удалено {len(dead)} нерабочих прокси")
    
    def delete_slow_proxies(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Удаление медленных прокси")
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("Удалить прокси медленнее чем (сек):"))
        speed_spin = QDoubleSpinBox()
        speed_spin.setRange(0.1, 60.0)
        speed_spin.setValue(2.0)
        layout.addWidget(speed_spin)
        
        buttons = QHBoxLayout()
        ok_btn = QPushButton("Удалить")
        cancel_btn = QPushButton("Отмена")
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
            QMessageBox.information(self, "Информация", f"Нет прокси медленнее {threshold}с")
            return
        
        reply = QMessageBox.question(self, "Подтверждение", f"Удалить {len(slow)} медленных прокси?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.proxies = [p for p in self.proxies if not (p.get('speed', 0) and float(p.get('speed', 0)) > threshold)]
            self.refresh_table()
            self.save_proxies()
            logger.info(f"🐢 Удалено {len(slow)} медленных прокси")
    
    def import_proxies(self):
        text, ok = QInputDialog.getMultiLineText(self, "Импорт прокси", "Введите прокси (IP:PORT):")
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
        QMessageBox.information(self, "Успех", f"✓ Импортировано {added} прокси")
        logger.info(f"✓ Импортировано {added} прокси")
    
    def clear_all(self):
        reply = QMessageBox.question(self, "Подтверждение", "Очистить ВСЕ прокси?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.proxies = []
            self.refresh_table()
            self.save_proxies()
            logger.info("🗑 Все прокси удалены")
    
    def toggle_proxy(self):
        """Переключает включение/отключение прокси"""
        if self.proxy_enabled:
            # Прокси включен - отключаем
            self.disable_proxy()
        else:
            # Прокси отключен - включаем
            self.enable_proxy()
    
    def enable_proxy(self):
        """Включает выбранный прокси"""
        row = self.table.currentRow()
        if row < 0 or row >= len(self.proxies):
            QMessageBox.warning(self, "Ошибка", "Выберите прокси из таблицы")
            return
        
        proxy = self.proxies[row]
        # Разрешаем включать ALIVE и SLOW прокси
        if proxy.get('status') not in ['alive', 'slow']:
            QMessageBox.warning(self, "Ошибка", f"Можно активировать только рабочие прокси (✅ ALIVE или 🐢 SLOW)\nСейчас: {proxy.get('status').upper()}")
            return
        
        try:
            import winreg, ctypes
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
            self.status_btn.setText(f"{status_emoji} ВКЛЮЧЕН: {proxy['ip']}:{proxy['port']}{speed_info}")
            self.status_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #00d084, stop:1 #00a86b);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #00a86b, stop:1 #008c47);
                }
            """)
            logger.info(f"✓ Прокси включен: {proxy['ip']}:{proxy['port']} ({proxy.get('status')}){speed_info}")
            QMessageBox.information(self, "✅ Успех", f"Прокси включен\n{proxy['ip']}:{proxy['port']}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось включить прокси: {e}")
            logger.error(f"✗ Ошибка: {e}")
    
    def disable_proxy(self):
        """Отключает прокси в Windows"""
        try:
            import winreg, ctypes
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
            
            self.proxy_enabled = False
            self.active_proxy = None
            self.save_settings()
            self.status_btn.setText("⚫ ПРОКСИ ВЫКЛЮЧЕН")
            self.status_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ff6b6b, stop:1 #d63031);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ff8787, stop:1 #e84118);
                }
            """)
            logger.info(f"✓ Прокси отключен")
            QMessageBox.information(self, "✅ Успех", "Прокси отключен\nВернулись на прямое подключение")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось отключить прокси: {e}")
            logger.error(f"✗ Ошибка отключения: {e}")
    
    def rotate_proxy(self):
        """Автоматически переключает на следующий живой прокси"""
        if not self.proxy_enabled:
            logger.info("⚠ Авторотация: прокси не включен, пропуск")
            return
        
        alive_proxies = [i for i, p in enumerate(self.proxies) if p.get('status') == 'alive']
        
        if not alive_proxies:
            logger.warning("⚠ Нет живых прокси для ротации")
            return
        
        # Выбираем случайный живой прокси
        next_idx = random.choice(alive_proxies)
        self.table.setCurrentCell(next_idx, 0)
        self.toggle_proxy()
        logger.info(f"🔄 Ротация: выбран прокси #{next_idx + 1}")
    
    def setup_auto_rotate(self):
        """Открывает диалог настройки авторотации"""
        dialog = QDialog(self)
        dialog.setWindowTitle("⚙ Авторотация прокси")
        dialog.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #333;
            }
            QSpinBox {
                background-color: white;
                color: #333;
                border: 2px solid #667eea;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
            }
            QCheckBox {
                color: #333;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #764ba2, stop:1 #667eea);
            }
        """)
        layout = QVBoxLayout(dialog)
        
        # Заголовок
        title = QLabel("🔄 Автоматическая смена прокси")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Включить авторотацию
        enable_checkbox = QCheckBox("✓ Включить авторотацию")
        enable_checkbox.setFont(QFont("Segoe UI", 11))
        enable_checkbox.setChecked(self.settings.get('auto_rotate', False))
        layout.addWidget(enable_checkbox)
        
        # Интервал
        layout.addWidget(QLabel("Интервал (секунды):"))
        interval_spin = QSpinBox()
        interval_spin.setRange(5, 3600)
        interval_spin.setValue(self.rotate_timer_interval)
        interval_spin.setSingleStep(5)
        interval_spin.setMinimumHeight(36)
        layout.addWidget(interval_spin)
        
        layout.addSpacing(15)
        layout.addWidget(QLabel("💡 Совет: Используй авторотацию чтобы менять прокси каждые N секунд"))
        
        # Кнопки
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("✓ СОХРАНИТЬ")
        cancel_btn = QPushButton("✖ ОТМЕНА")
        ok_btn.setMinimumHeight(36)
        cancel_btn.setMinimumHeight(36)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e0e0e0, stop:1 #ccc);
                color: #333;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-weight: bold;
            }
        """)
        
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
                    "✅ Авторотация включена",
                    f"Прокси будет меняться каждые {interval} сек"
                )
                logger.info(f"✓ Авторотация включена: интервал {interval} сек")
            else:
                self.rotate_timer.stop()
                QMessageBox.information(
                    self,
                    "⏹ Авторотация отключена",
                    "Авторотация прокси отключена"
                )
                logger.info("✓ Авторотация отключена")
            
            dialog.accept()
        
        ok_btn.clicked.connect(save_settings)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec_()
    
    def update_my_ip(self):
        def check_ip():
            try:
                response = requests.get('https://api.ipify.org?format=json', timeout=3)
                ip = response.json().get('ip', 'Unknown')
                QTimer.singleShot(0, lambda: self.ip_label.setText(f"IP: {ip}"))
            except:
                QTimer.singleShot(0, lambda: self.ip_label.setText("IP: Unknown"))
        
        threading.Thread(target=check_ip, daemon=True).start()
    
    def closeEvent(self, event):
        """[ 💾 SHUTDOWN ] Сохраняет состояние и данные при завершении работы"""
        logger.info("=" * 70)
        logger.info("[ 🔓 SHUTDOWN ] Инициирующий финальное сохранение данных...")
        logger.info("=" * 70)
        
        try:
            logger.info(f"[ 📊 AUDIT ] Количество нодов в памяти: {len(self.proxies)}")
            
            # ► Валидация и очистка некорректных записей
            before = len(self.proxies)
            cleaned = [p for p in self.proxies if p.get('ip') and p.get('port')]
            logger.info(f"[ 🧹 CLEANUP ] Удалено {before - len(cleaned)} некорректных записей")
            self.proxies = cleaned
            
            # ► Синхронизация прокси-базы
            logger.info(f"[ 💾 SYNC ] Сохранение {len(self.proxies)} нодов на диск...")
            self.save_proxies()
            
            # ► Синхронизация конфигурации
            logger.info(f"[ 💾 SYNC ] Сохранение параметров конфигурации...")
            self.save_settings()
            
            # ► Верификация целостности файлов
            if CONFIG_FILE.exists():
                size = CONFIG_FILE.stat().st_size
                logger.info(f"[ ✅ VERIFIED ] proxies.json: {size} байт")
            else:
                logger.error(f"[ ❌ CRITICAL ] proxies.json не найден!")
            
            if SETTINGS_FILE.exists():
                size = SETTINGS_FILE.stat().st_size
                logger.info(f"[ ✅ VERIFIED ] settings.json: {size} байт")
            else:
                logger.error(f"[ ❌ CRITICAL ] settings.json не найден!")
            
            logger.info("=" * 70)
            logger.info("[ ✅ SHUTDOWN ] Приложение закрыто. Данные успешно сохранены.")
            logger.info("=" * 70)
        except Exception as e:
            logger.error(f"[ ❌ FATAL ] Критическая ошибка при завершении: {e}")
            import traceback
            logger.error(f"[ STACK ] {traceback.format_exc()}")
        
        event.accept()
    
    def setup_table_context_menu(self):
        """Добавляет контекстное меню для таблицы"""
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_table_context_menu)
    
    def show_table_context_menu(self, pos):
        """Отображает контекстное меню при клике правой кнопкой мыши"""
        index = self.table.rowAt(pos.y())
        if index < 0 or index >= len(self.proxies):
            return
        
        menu = QMenu(self)
        proxy = self.proxies[index]
        is_favorite = proxy.get('favorite', False)
        
        # Пункт меню для избранного
        if is_favorite:
            action = menu.addAction("★ Удалить из избранного")
        else:
            action = menu.addAction("☆ Добавить в избранное")
        
        action.triggered.connect(lambda: self.toggle_favorite(index))
        
        # Еще несколько полезных пунктов
        menu.addSeparator()
        
        copy_action = menu.addAction("📋 Копировать IP:Port")
        copy_action.triggered.connect(lambda: self.copy_proxy_to_clipboard(index))
        
        menu.exec_(self.table.mapToGlobal(pos))
    
    def toggle_favorite(self, index):
        """[ ⭐ FAVORITE ] Добавляет/удаляет прокси-ноду в список избранного"""
        if index < 0 or index >= len(self.proxies):
            return
        
        self.proxies[index]['favorite'] = not self.proxies[index].get('favorite', False)
        self.save_proxies()  # ► Немедленная синхронизация
        self.refresh_table()
        
        is_favorite = self.proxies[index]['favorite']
        status = "добавлена в" if is_favorite else "удалена из"
        logger.info(f"[ ⭐ FAVORITE ] Нода #{index + 1} {status} список избранных")
    
    def copy_proxy_to_clipboard(self, index):
        """[ 📋 CLIPBOARD ] Копирует адрес прокси-ноды в буфер обмена"""
        if index < 0 or index >= len(self.proxies):
            return
        
        proxy = self.proxies[index]
        proxy_str = f"{proxy['ip']}:{proxy['port']}"
        
        clipboard = QApplication.clipboard()
        clipboard.setText(proxy_str)
        
        logger.info(f"[ 📋 COPIED ] {proxy_str} скопирован в буфер")
        QMessageBox.information(self, "[ ✅ SUCCESS ]", f"Скопировано в буфер обмена:\n{proxy_str}")


# ============================================================================
# 🚀 ТОЧКА ВХОДА (Application Launcher)
# ============================================================================
def main():
    logger.info("[ 🚀 LAUNCH ] Инициализация Qt приложения...")
    app = QApplication(sys.argv)
    logger.info("[ ✓ QT_READY ] Qt готов к работе")
    
    window = ProxySwitcherPro()
    logger.info("[ ✓ WINDOW_CREATED ] Главное окно создано")
    
    window.show()
    logger.info("[ ✓ WINDOW_SHOWN ] Приложение отображено на экране")
    logger.info("[ ► RUNNING ] Вход в цикл обработки событий...")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    logger.info("\n" + "="*70)
    logger.info("[ ⚡ PROXY_SWITCHER_PROFESSIONAL_v5.2 ]")
    logger.info("[ Mr. Robot Edition - Elite Anonymity Toolkit ]")
    logger.info("="*70)
    main()
    logger.info("="*70)
    logger.info("[ ✅ PROGRAM_TERMINATED ] Завершение работы")
    logger.info("="*70)
