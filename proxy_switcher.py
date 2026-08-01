#!/usr/bin/env python3
# Proxy Switcher Pro - управление прокси
# v2.0.0

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
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# логирование
try:
    from loguru import logger
    LOGURU = True
except ImportError:
    LOGURU = False
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
    logger = logging.getLogger("ProxySwitcher")

if LOGURU:
    try:
        LOG_DIR = Path.home() / "Documents" / "ProxySwitcher" / "logs"
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        logger.remove()
        logger.add(sys.stderr, format="<level>{time:HH:mm:ss}</level> | <level>{level: <8}</level> | {message}", level="INFO", colorize=True)
        logger.add(LOG_DIR / "proxy_switcher_{time:YYYY-MM-DD}.log", rotation="500 MB", retention="10 days", level="DEBUG")
    except:
        pass

logger.info("Proxy Switcher Pro v2.0.0 - запуск")

APP_NAME = "Proxy Switcher Pro"
VERSION = "2.0.0"
CONFIG_DIR = Path.home() / "Documents" / "ProxySwitcher"
CONFIG_FILE = CONFIG_DIR / "proxies.json"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

IS_WINDOWS = platform.system() == "Windows"

try:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    logger.error(f"Ошибка конфигурации: {e}")

# источники прокси
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

logger.info(f"Загружено {len(PROXY_SOURCES)} источников прокси")


# ============================================================
# Тема (чёрно-белая)
# ============================================================
class Theme:
    BG = "#1a1a1a"
    BG_ALT = "#2d2d2d"
    BG_HOVER = "#3d3d3d"
    FG = "#ffffff"
    FG_DIM = "#aaaaaa"
    FG_DARK = "#666666"
    BORDER = "#444444"
    SUCCESS = "#4caf50"
    WARNING = "#ff9800"
    ERROR = "#f44336"
    SELECTION = "#555555"

    @staticmethod
    def stylesheet():
        return f"""
            QMainWindow, QDialog {{ background-color: {Theme.BG}; }}
            QWidget {{ background-color: {Theme.BG}; color: {Theme.FG}; font-family: 'Segoe UI', Arial; }}
            QLabel {{ color: {Theme.FG}; }}
            QLabel#title {{ font-size: 16px; font-weight: bold; }}
            QLabel#subtitle {{ font-size: 11px; color: {Theme.FG_DIM}; }}
            QLabel#stats {{ font-size: 11px; color: {Theme.FG_DIM}; padding: 4px; }}
            QPushButton {{
                background-color: {Theme.BG_ALT}; color: {Theme.FG};
                border: 1px solid {Theme.BORDER}; border-radius: 4px;
                padding: 8px 16px; font-weight: bold; font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {Theme.BG_HOVER}; border-color: {Theme.FG_DIM}; }}
            QPushButton:pressed {{ background-color: {Theme.BG}; }}
            QPushButton:disabled {{ background-color: {Theme.BG}; color: {Theme.FG_DARK}; }}
            QPushButton#primary {{ background-color: {Theme.FG}; color: {Theme.BG}; border: none; }}
            QPushButton#primary:hover {{ background-color: {Theme.FG_DIM}; }}
            QPushButton#danger {{ background-color: {Theme.BG_ALT}; color: {Theme.ERROR}; border: 1px solid {Theme.ERROR}; }}
            QPushButton#danger:hover {{ background-color: {Theme.ERROR}; color: {Theme.FG}; }}
            QTableWidget {{
                background-color: {Theme.BG}; alternate-background-color: {Theme.BG_ALT};
                gridline-color: {Theme.BORDER}; border: 1px solid {Theme.BORDER};
                color: {Theme.FG}; selection-background-color: {Theme.SELECTION};
            }}
            QTableWidget::item {{ padding: 6px; border: none; }}
            QTableWidget::item:selected {{ background-color: {Theme.SELECTION}; color: {Theme.FG}; }}
            QHeaderView::section {{
                background-color: {Theme.BG_ALT}; color: {Theme.FG};
                padding: 8px; border: 1px solid {Theme.BORDER}; font-weight: bold;
            }}
            QProgressBar {{
                border: 1px solid {Theme.BORDER}; border-radius: 3px;
                background-color: {Theme.BG_ALT}; text-align: center; color: {Theme.FG}; height: 20px;
            }}
            QProgressBar::chunk {{ background-color: {Theme.FG}; border-radius: 2px; }}
            QScrollBar:vertical {{ width: 12px; background-color: {Theme.BG}; }}
            QScrollBar::handle:vertical {{ background-color: {Theme.BG_HOVER}; border-radius: 6px; min-height: 20px; }}
            QScrollBar::handle:vertical:hover {{ background-color: {Theme.FG_DIM}; }}
            QMenu {{ background-color: {Theme.BG_ALT}; color: {Theme.FG}; border: 1px solid {Theme.BORDER}; }}
            QMenu::item {{ padding: 8px 24px; }}
            QMenu::item:selected {{ background-color: {Theme.BG_HOVER}; }}
            QSpinBox, QDoubleSpinBox, QLineEdit, QTextEdit {{
                background-color: {Theme.BG_ALT}; color: {Theme.FG};
                border: 1px solid {Theme.BORDER}; border-radius: 4px; padding: 6px;
            }}
            QCheckBox {{ color: {Theme.FG}; }}
            QCheckBox::indicator {{
                width: 16px; height: 16px; border: 1px solid {Theme.BORDER};
                background-color: {Theme.BG_ALT};
            }}
            QCheckBox::indicator:checked {{ background-color: {Theme.FG}; border-color: {Theme.FG}; }}
            QMessageBox {{ background-color: {Theme.BG}; }}
        """


class SplashScreen(QWidget):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        screen = QApplication.primaryScreen()
        self.setGeometry(screen.geometry())
        self.setStyleSheet(f"QWidget {{ background-color: {Theme.BG}; }}")

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

        self.status = QLabel("Загрузка...")
        self.status.setFont(QFont("Segoe UI", 12))
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet(f"color: {Theme.FG_DIM};")
        layout.addWidget(self.status)

        self.progress = QProgressBar()
        self.progress.setMaximumWidth(400)
        self.progress.setStyleSheet(f"""
            QProgressBar {{ border: 1px solid {Theme.BORDER}; border-radius: 3px; background: {Theme.BG_ALT}; }}
            QProgressBar::chunk {{ background: {Theme.FG}; border-radius: 2px; }}
        """)
        layout.addWidget(self.progress, alignment=Qt.AlignCenter)

        layout.addStretch()
        self.progress_value = 0
        self.animate()

    def animate(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(50)

    def update_progress(self):
        self.progress_value += 1
        statuses = ["Загрузка конфигурации...", "Инициализация...", "Загрузка UI...", "Подготовка окна...", "Готово"]
        idx = min(self.progress_value // 20, len(statuses) - 1)
        self.status.setText(statuses[idx])
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
        logger.info(f"[GRABBER] Инициализирован (max={max_proxies})")

    def stop(self):
        self._is_running = False
        logger.info("[GRABBER] Остановлен")

    def fetch_url(self, url, timeout=10):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            r = requests.get(url, headers=headers, timeout=timeout)
            r.raise_for_status()
            return r.text
        except requests.exceptions.Timeout:
            logger.warning(f"[TIMEOUT] {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning(f"[CONN_ERR] {url}")
            return None
        except Exception as e:
            logger.error(f"[FETCH_ERR] {url}: {e}")
            return None

    def parse_table_proxies(self, html):
        try:
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('table')
            if not table:
                return []
            proxies = []
            for row in table.find_all('tr')[1:]:
                try:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        ip = cols[0].text.strip()
                        port = cols[1].text.strip()
                        if ip and port and self.is_valid_ip(ip) and port.isdigit():
                            proxies.append((ip, port))
                except:
                    continue
            return proxies
        except Exception as e:
            logger.error(f"[PARSE_ERR] {e}")
            return []

    def is_valid_ip(self, ip):
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            return all(0 <= int(p) <= 255 for p in parts)
        except:
            return False

    def parse_text_proxies(self, text):
        try:
            if not text:
                return []
            pattern = r'(\d+\.\d+\.\d+\.\d+):(\d+)'
            matches = re.findall(pattern, text)
            proxies = []
            for ip, port in matches:
                try:
                    if self.is_valid_ip(ip) and 1 <= int(port) <= 65535:
                        proxies.append((ip, port))
                except:
                    continue
            return proxies
        except Exception as e:
            logger.error(f"[PARSE_ERR] {e}")
            return []

    def add_proxy(self, ip, port, proxy_type='HTTP'):
        if len(self.found_proxies) >= self.max_proxies:
            self.stop()
            return
        key = f"{ip}:{port}"
        if key not in self.seen:
            self.seen.add(key)
            self.found_proxies.append({
                'ip': ip, 'port': port, 'type': proxy_type.upper(),
                'name': f"Proxy_{ip}", 'login': '', 'password': '',
                'status': 'fresh', 'speed': '', 'anonymity': 'unknown', 'country': '🌍',
            })
            self.proxy_found.emit(ip, port, proxy_type)

    def run(self):
        logger.info(f"[GRABBER] Сбор из {len(PROXY_SOURCES)} источников")
        total = len(PROXY_SOURCES)

        for i, url in enumerate(PROXY_SOURCES):
            if not self._is_running or len(self.found_proxies) >= self.max_proxies:
                break
            self.progress.emit(int((i / total) * 100), f"Сбор... {len(self.found_proxies)}/{self.max_proxies}")

            if 'socks5' in url.lower():
                ptype = 'SOCKS5'
            elif 'socks4' in url.lower():
                ptype = 'SOCKS4'
            else:
                ptype = 'HTTP'

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
                    self.add_proxy(ip, port, ptype)
            except Exception as e:
                logger.error(f"[SOURCE_ERR] {url}: {e}")
                continue

        logger.info(f"[GRABBER] Собрано {len(self.found_proxies)} прокси")
        self.progress.emit(100, f"Готово: {len(self.found_proxies)} прокси")
        self.finished.emit(self.found_proxies)


# ============================================================
# Проверка прокси
# ============================================================
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
        logger.info(f"[CHECKER] Проверка {len(proxies)} прокси")

    def stop(self):
        self._is_running = False

    def check_single_proxy(self, proxy, index):
        results = {'status': 'dead', 'speed': 0, 'anonymity': 'unknown', 'country': '🌍', 'error': ''}
        ip = proxy.get('ip', '')
        port = proxy.get('port', '')
        ptype = proxy.get('type', 'HTTP').upper()

        if not ip or not port:
            return results

        # проверяем доступность порта
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, int(port)))
            sock.close()
            if result != 0:
                return results
        except:
            return results

        if ptype in ['HTTP', 'HTTPS']:
            try:
                proxy_str = f"http://{ip}:{port}"
                pd = {'http': proxy_str, 'https': proxy_str}
                start = time.time()
                r = requests.get('http://httpbin.org/ip', proxies=pd, timeout=3, headers={'User-Agent': 'Mozilla/5.0'})
                rt = time.time() - start
                if r.status_code == 200:
                    results['status'] = 'alive'
                    results['speed'] = round(rt, 2)
                    try:
                        data = r.json()
                        proxy_ip = data.get('origin', '')
                        results['anonymity'] = 'transparent' if proxy_ip == ip else 'elite'
                    except:
                        results['anonymity'] = 'anonymous'
                else:
                    results['status'] = 'slow'
                    results['speed'] = round(rt, 2)
                    results['error'] = f'HTTP {r.status_code}'
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

        elif ptype in ['SOCKS4', 'SOCKS5']:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                start = time.time()
                result = sock.connect_ex((ip, int(port)))
                sock.close()
                rt = time.time() - start
                if result == 0:
                    results['status'] = 'alive'
                    results['speed'] = round(rt, 2)
                    results['anonymity'] = 'elite'
                else:
                    results['status'] = 'slow'
                    results['speed'] = 2.0
            except:
                results['status'] = 'dead'

        results['country'] = self._get_country_by_ip(ip)
        return results

    def _get_country_by_ip(self, ip):
        # пробуем несколько сервисов
        try:
            r = requests.get(f'http://ip-api.com/json/{ip}', timeout=1)
            if r.status_code == 200:
                c = r.json().get('country')
                if c:
                    return c[:2]
        except:
            pass
        try:
            r = requests.get(f'https://ipapi.co/{ip}/json/', timeout=1)
            if r.status_code == 200:
                c = r.json().get('country_code')
                if c:
                    return c
        except:
            pass
        return '🌍'

    def run(self):
        total = len(self.proxies)
        logger.info(f"[CHECKER] Запуск проверки {total} прокси")

        try:
            r = requests.get('https://api.ipify.org?format=json', timeout=2)
            real_ip = r.json().get('ip', 'Unknown')
            self.ip_checked_signal.emit(real_ip)
        except:
            pass

        completed = 0
        max_workers = min(self.settings.get('threads', 50), 100)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for i, proxy in enumerate(self.proxies):
                if not self._is_running:
                    break
                futures[executor.submit(self.check_single_proxy, proxy, i)] = i

            for future in concurrent.futures.as_completed(futures):
                if not self._is_running:
                    break
                idx = futures[future]
                try:
                    result = future.result(timeout=2)
                    self.proxies[idx].update(result)
                    self.proxy_checked.emit(idx, result)
                except Exception as e:
                    logger.error(f"[CHECK_ERR] #{idx}: {e}")
                completed += 1
                self.progress.emit(int((completed / total) * 100), f"Проверено {completed}/{total}")

        alive = sum(1 for p in self.proxies if p.get('status') == 'alive')
        slow = sum(1 for p in self.proxies if p.get('status') == 'slow')
        dead = sum(1 for p in self.proxies if p.get('status') == 'dead')
        logger.info(f"[CHECKER] Готово: {alive} живых | {slow} медленных | {dead} мертвых")


# ============================================================
# Главное окно
# ============================================================
class ProxySwitcherPro(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info(f"Инициализация {APP_NAME} v{VERSION}")

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
            self.load_proxies()
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            raise

        self.ip_timer = QTimer()
        self.ip_timer.timeout.connect(self.update_my_ip)
        self.ip_timer.start(15000)

        self.rotate_timer = QTimer()
        self.rotate_timer.timeout.connect(self.rotate_proxy)
        self.rotate_timer_interval = 60

        QTimer.singleShot(1000, self.update_my_ip)

    def default_settings(self):
        return {'theme': 'dark', 'timeout': 10, 'threads': 30, 'auto_rotate': False, 'last_proxy': None}

    def init_ui(self):
        self.setWindowTitle(f"Proxy Switcher Pro v{VERSION}")
        self.setGeometry(100, 100, 1200, 700)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # верхняя панель
        top = QHBoxLayout()
        title = QLabel(f"Proxy Switcher Pro - v{VERSION}")
        title.setObjectName("title")
        top.addWidget(title)
        top.addStretch()

        self.ip_label = QLabel("IP: ...")
        self.ip_label.setObjectName("subtitle")
        top.addWidget(self.ip_label)

        self.status_btn = QPushButton("OFFLINE")
        self.status_btn.setMaximumWidth(160)
        self.status_btn.clicked.connect(self.toggle_proxy)
        top.addWidget(self.status_btn)
        layout.addLayout(top)

        # кнопки
        btns = QHBoxLayout()
        buttons = [
            ("Grab Proxies", self.grab_proxies),
            ("Verify All", self.check_all_proxies),
            ("Delete Dead", self.delete_dead_proxies),
            ("Delete Slow", self.delete_slow_proxies),
            ("Import", self.import_proxies),
            ("Auto Rotate", self.setup_auto_rotate),
            ("Clear All", self.clear_all),
        ]
        for text, cb in buttons:
            btn = QPushButton(text)
            btn.setMinimumWidth(100)
            btn.clicked.connect(cb)
            btns.addWidget(btn)
        layout.addLayout(btns)

        # таблица
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["#", "IP", "PORT", "TYPE", "STATUS", "SPEED", "ANONYMITY", "COUNTRY"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.setup_table_context_menu()
        layout.addWidget(self.table)

        # прогресс
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(25)
        layout.addWidget(self.progress_bar)

        # статистика
        self.stats_label = QLabel("Total: 0 | Alive: 0 | Slow: 0 | Dead: 0")
        self.stats_label.setObjectName("stats")
        layout.addWidget(self.stats_label)

    def apply_theme(self):
        self.setStyleSheet(Theme.stylesheet())

    def load_proxies(self):
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, encoding='utf-8') as f:
                    self.proxies = json.load(f)
                logger.info(f"Загружено {len(self.proxies)} прокси")
            self.refresh_table()
        except Exception as e:
            logger.error(f"Ошибка загрузки: {e}")

    def save_proxies(self):
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.proxies, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")

    def load_settings(self):
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, encoding='utf-8') as f:
                    self.settings.update(json.load(f))
        except Exception as e:
            logger.error(f"Ошибка загрузки настроек: {e}")

    def save_settings(self):
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")

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

            ptype = proxy.get('type', 'HTTP')
            emoji = '🔗' if ptype == 'HTTP' else '🔒' if ptype == 'HTTPS' else '🌐'
            if 'SOCKS5' in ptype:
                emoji = '🔐'
            elif 'SOCKS4' in ptype:
                emoji = '🔒'
            type_item = QTableWidgetItem(f"{emoji} {ptype}")
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
            speed_item = QTableWidgetItem(f"{speed}s" if speed else "-")
            speed_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, speed_item)

            anon = proxy.get('anonymity', 'unknown')
            anon_emoji = '🟢' if anon == 'elite' else '🟡' if anon == 'anonymous' else '🔴'
            anon_item = QTableWidgetItem(f"{anon_emoji} {anon}")
            anon_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 6, anon_item)

            country = proxy.get('country', '🌍')
            country_item = QTableWidgetItem(str(country))
            country_item.setTextAlignment(Qt.AlignCenter)
            if proxy.get('favorite', False):
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
        dialog = QDialog(self)
        dialog.setWindowTitle("Настройки сбора прокси")
        dialog.setStyleSheet(Theme.stylesheet())
        layout = QVBoxLayout(dialog)

        title = QLabel("Сколько прокси собрать?")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)

        desc = QLabel("Введите количество (10-500):\nБольше = дольше")
        desc.setFont(QFont("Segoe UI", 10))
        desc.setStyleSheet(f"color: {Theme.FG_DIM};")
        layout.addWidget(desc)

        spinbox = QSpinBox()
        spinbox.setRange(10, 500)
        spinbox.setValue(100)
        spinbox.setSingleStep(10)
        spinbox.setMinimumHeight(40)
        layout.addWidget(spinbox)

        add_checkbox = QCheckBox(f"Добавить к существующим ({len(self.proxies)})")
        add_checkbox.setChecked(len(self.proxies) > 0)
        layout.addWidget(add_checkbox)

        btns = QHBoxLayout()
        ok_btn = QPushButton("СОБРАТЬ")
        ok_btn.setObjectName("primary")
        cancel_btn = QPushButton("ОТМЕНА")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        if dialog.exec_() != QDialog.Accepted:
            return

        count = spinbox.value()
        add_to_existing = add_checkbox.isChecked()

        reply = QMessageBox.question(self, "Подтверждение",
            f"Будет {'добавлено' if add_to_existing else 'собрано'} {count} прокси?\n\nЭто может занять 2-5 минут...",
            QMessageBox.Yes | QMessageBox.No)
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

    def on_grab_finished(self, proxies):
        self.proxies.extend(proxies)
        # убираем дубликаты
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
            QMessageBox.information(self, "Готово",
                f"Всего прокси: {total}\n\nСохранено: {CONFIG_FILE}\n\nТеперь нажми 'Verify All'!")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось собрать прокси\n\nПопробуй позже")

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
            if self.proxies[index].get('favorite', False):
                country_item.setText(f"⭐ {country}")
                country_item.setForeground(QColor('#FFD700'))
            self.table.setItem(index, 7, country_item)

            self.proxies[index]['status'] = status
            self.proxies[index]['speed'] = speed
            self.proxies[index]['country'] = country
            self.proxies[index]['anonymity'] = result.get('anonymity', 'unknown')
        except Exception as e:
            logger.error(f"[UPDATE_ERR] {e}")

    def on_check_finished(self, proxies):
        for i, result in enumerate(proxies):
            if i < len(self.proxies):
                self.proxies[i]['status'] = result.get('status', 'unknown')
                self.proxies[i]['speed'] = result.get('speed', '')
                self.proxies[i]['country'] = result.get('country', '🌍')
                self.proxies[i]['anonymity'] = result.get('anonymity', 'unknown')

        self.refresh_table()
        self.progress_bar.setVisible(False)
        self.save_proxies()

        alive = sum(1 for p in self.proxies if p.get('status') == 'alive')
        dead = sum(1 for p in self.proxies if p.get('status') == 'dead')
        self.status_btn.setText(f"VERIFIED: {alive} alive | {dead} dead")

    def delete_dead_proxies(self):
        dead = [p for p in self.proxies if p.get('status') == 'dead']
        if not dead:
            QMessageBox.information(self, "Инфо", "Нет мертвых прокси")
            return

        reply = QMessageBox.question(self, "Подтверждение", f"Удалить {len(dead)} мертвых прокси?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.proxies = [p for p in self.proxies if p.get('status') != 'dead']
            self.refresh_table()
            self.save_proxies()

    def delete_slow_proxies(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Удалить медленные прокси")
        dialog.setStyleSheet(Theme.stylesheet())
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Удалить прокси медленнее (сек):"))
        speed_spin = QDoubleSpinBox()
        speed_spin.setRange(0.1, 60.0)
        speed_spin.setValue(2.0)
        layout.addWidget(speed_spin)

        btns = QHBoxLayout()
        ok_btn = QPushButton("Удалить")
        ok_btn.setObjectName("danger")
        cancel_btn = QPushButton("Отмена")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        if dialog.exec_() != QDialog.Accepted:
            return

        threshold = speed_spin.value()
        slow = [p for p in self.proxies if p.get('speed', 0) and float(p.get('speed', 0)) > threshold]

        if not slow:
            QMessageBox.information(self, "Инфо", f"Нет прокси медленнее {threshold}s")
            return

        reply = QMessageBox.question(self, "Подтверждение", f"Удалить {len(slow)} медленных прокси?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.proxies = [p for p in self.proxies if not (p.get('speed', 0) and float(p.get('speed', 0)) > threshold)]
            self.refresh_table()
            self.save_proxies()

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
        QMessageBox.information(self, "Успех", f"Импортировано {added} прокси")

    def clear_all(self):
        reply = QMessageBox.question(self, "Подтверждение", "Очистить ВСЕ прокси?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.proxies = []
            self.refresh_table()
            self.save_proxies()

    def toggle_proxy(self):
        if self.proxy_enabled:
            self.disable_proxy()
        else:
            self.enable_proxy()

    def enable_proxy(self):
        if not IS_WINDOWS:
            QMessageBox.warning(self, "Ошибка", "Системная настройка прокси доступна только на Windows")
            return

        row = self.table.currentRow()
        if row < 0 or row >= len(self.proxies):
            QMessageBox.warning(self, "Ошибка", "Выберите прокси из таблицы")
            return

        proxy = self.proxies[row]
        if proxy.get('status') not in ['alive', 'slow']:
            QMessageBox.warning(self, "Ошибка", f"Можно активировать только рабочие прокси (ALIVE или SLOW)\nТекущий: {proxy.get('status').upper()}")
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
            emoji = "🟢" if proxy.get('status') == 'alive' else "🟡"
            speed_info = f" ({proxy.get('speed', '?')}s)" if proxy.get('speed') else ""
            self.status_btn.setText(f"{emoji} ENABLED: {proxy['ip']}:{proxy['port']}{speed_info}")
            self.status_btn.setStyleSheet(f"""
                QPushButton {{ background-color: {Theme.SUCCESS}; color: white; border: none; border-radius: 4px; padding: 8px 16px; font-weight: bold; }}
                QPushButton:hover {{ background-color: #388e3c; }}
            """)
            QMessageBox.information(self, "Успех", f"Прокси включен\n{proxy['ip']}:{proxy['port']}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось включить прокси: {e}")

    def disable_proxy(self):
        if not IS_WINDOWS:
            QMessageBox.warning(self, "Ошибка", "Системная настройка прокси доступна только на Windows")
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
                QPushButton {{ background-color: {Theme.ERROR}; color: white; border: none; border-radius: 4px; padding: 8px 16px; font-weight: bold; }}
                QPushButton:hover {{ background-color: #d32f2f; }}
            """)
            QMessageBox.information(self, "Успех", "Прокси выключен\nПрямое соединение")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось выключить прокси: {e}")

    def rotate_proxy(self):
        if not self.proxy_enabled:
            return

        alive = [i for i, p in enumerate(self.proxies) if p.get('status') == 'alive']
        if not alive:
            return

        next_idx = random.choice(alive)
        self.table.setCurrentCell(next_idx, 0)
        self.toggle_proxy()

    def setup_auto_rotate(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Авторотация")
        dialog.setStyleSheet(Theme.stylesheet())
        layout = QVBoxLayout(dialog)

        title = QLabel("Автоматическая ротация прокси")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)

        enable_checkbox = QCheckBox("Включить авторотацию")
        enable_checkbox.setChecked(self.settings.get('auto_rotate', False))
        layout.addWidget(enable_checkbox)

        layout.addWidget(QLabel("Интервал (секунд):"))
        interval_spin = QSpinBox()
        interval_spin.setRange(5, 3600)
        interval_spin.setValue(self.rotate_timer_interval)
        interval_spin.setSingleStep(5)
        interval_spin.setMinimumHeight(36)
        layout.addWidget(interval_spin)

        layout.addSpacing(15)
        layout.addWidget(QLabel("Совет: используйте авторотацию для смены прокси каждые N секунд"))

        btns = QHBoxLayout()
        ok_btn = QPushButton("СОХРАНИТЬ")
        ok_btn.setObjectName("primary")
        cancel_btn = QPushButton("ОТМЕНА")
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        def save_settings():
            enabled = enable_checkbox.isChecked()
            interval = interval_spin.value()

            self.settings['auto_rotate'] = enabled
            self.rotate_timer_interval = interval
            self.save_settings()

            if enabled:
                self.rotate_timer.start(interval * 1000)
                QMessageBox.information(self, "Авторотация", f"Прокси будет меняться каждые {interval} сек")
            else:
                self.rotate_timer.stop()
                QMessageBox.information(self, "Авторотация", "Авторотация выключена")

            dialog.accept()

        ok_btn.clicked.connect(save_settings)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec_()

    def update_my_ip(self):
        def check_ip():
            try:
                r = requests.get('https://api.ipify.org?format=json', timeout=3)
                ip = r.json().get('ip', 'Unknown')
                QTimer.singleShot(0, lambda: self.ip_label.setText(f"IP: {ip}"))
            except:
                QTimer.singleShot(0, lambda: self.ip_label.setText("IP: Unknown"))

        threading.Thread(target=check_ip, daemon=True).start()

    def closeEvent(self, event):
        logger.info("Закрытие приложения, сохранение данных...")
        try:
            self.save_proxies()
            self.save_settings()
        except Exception as e:
            logger.error(f"Ошибка при закрытии: {e}")
        event.accept()

    def setup_table_context_menu(self):
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_table_context_menu)

    def show_table_context_menu(self, pos):
        index = self.table.rowAt(pos.y())
        if index < 0 or index >= len(self.proxies):
            return

        menu = QMenu(self)
        proxy = self.proxies[index]
        is_favorite = proxy.get('favorite', False)

        if is_favorite:
            action = menu.addAction("★ Убрать из избранного")
        else:
            action = menu.addAction("☆ Добавить в избранное")
        action.triggered.connect(lambda: self.toggle_favorite(index))

        menu.addSeparator()

        copy_action = menu.addAction("📋 Копировать IP:Port")
        copy_action.triggered.connect(lambda: self.copy_proxy_to_clipboard(index))

        menu.exec_(self.table.mapToGlobal(pos))

    def toggle_favorite(self, index):
        if index < 0 or index >= len(self.proxies):
            return

        self.proxies[index]['favorite'] = not self.proxies[index].get('favorite', False)
        self.save_proxies()
        self.refresh_table()

    def copy_proxy_to_clipboard(self, index):
        if index < 0 or index >= len(self.proxies):
            return

        proxy = self.proxies[index]
        proxy_str = f"{proxy['ip']}:{proxy['port']}"
        QApplication.clipboard().setText(proxy_str)
        QMessageBox.information(self, "Успех", f"Скопировано:\n{proxy_str}")


# ============================================================
# Запуск
# ============================================================
def main():
    app = QApplication(sys.argv)

    splash = SplashScreen()
    splash.show()

    def create_main_window():
        window = ProxySwitcherPro()
        window.show()
        return window

    splash.finished.connect(create_main_window)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()


