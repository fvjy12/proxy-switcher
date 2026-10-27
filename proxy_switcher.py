#!/usr/bin/env python3

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
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

try:
    from loguru import logger
    LOGURU = True
except ImportError:
    LOGURU = False
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
    logger = logging.getLogger("ProxySwitcher")

APP_NAME = "Proxy Switcher Pro"
VERSION = "2.2.1"

if LOGURU:
    try:
        LOG_DIR = Path.home() / "Documents" / "ProxySwitcher" / "logs"
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        logger.remove()
        logger.add(sys.stderr, format="<level>{time:HH:mm:ss}</level> | <level>{level: <8}</level> | {message}", level="INFO", colorize=True)
        logger.add(LOG_DIR / "proxy_switcher_{time:YYYY-MM-DD}.log", rotation="500 MB", retention="10 days", level="DEBUG")
    except:
        pass

logger.info(f"{APP_NAME} v{VERSION} - запуск")

try:
    import socks
    SOCKS_SUPPORTED = True
except ImportError:
    SOCKS_SUPPORTED = False
    logger.warning("PySocks не установлен - SOCKS-прокси будут проверяться только по TCP-порту")

CONFIG_DIR = Path.home() / "Documents" / "ProxySwitcher"
CONFIG_FILE = CONFIG_DIR / "proxies.json"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

IS_WINDOWS = platform.system() == "Windows"

# Стандартный список исключений WinINET: локальные адреса не ходят через прокси
PROXY_OVERRIDE = ("localhost;127.*;10.*;172.16.*;172.17.*;172.18.*;172.19.*;172.20.*;"
                  "172.21.*;172.22.*;172.23.*;172.24.*;172.25.*;172.26.*;172.27.*;172.28.*;"
                  "172.29.*;172.30.*;172.31.*;192.168.*;<local>")

try:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    logger.error(f"Ошибка конфигурации: {e}")

PROXY_SOURCES = [
    ("https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all&format=textplain", "HTTP"),
    ("https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt", "HTTP"),
    ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt", "HTTP"),
    ("https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt", "HTTP"),
    ("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt", "HTTP"),
    ("https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt", "HTTP"),
    ("https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt", "HTTP"),
    ("https://www.sslproxies.org/", "HTTP"),
    ("https://www.free-proxy-list.net/", "HTTP"),
    ("https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=all&ssl=all&anonymity=all&format=textplain", "SOCKS5"),
    ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt", "SOCKS5"),
    ("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt", "SOCKS5"),
    ("https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt", "SOCKS5"),
    ("https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt", "SOCKS5"),
    ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt", "SOCKS4"),
    ("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt", "SOCKS4"),

    ("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt", "HTTP"),
]

logger.info(f"Загружено {len(PROXY_SOURCES)} источников прокси")

THEMES = {
    'dark': {
        'BG': '#1a1a1a', 'BG_ALT': '#2d2d2d', 'BG_HOVER': '#3d3d3d',
        'FG': '#ffffff', 'FG_DIM': '#aaaaaa', 'FG_DARK': '#666666',
        'BORDER': '#444444', 'SUCCESS': '#4caf50', 'WARNING': '#ff9800',
        'ERROR': '#f44336', 'SELECTION': '#555555',
    },
    'light': {
        'BG': '#f5f5f5', 'BG_ALT': '#ffffff', 'BG_HOVER': '#e2e2e2',
        'FG': '#1a1a1a', 'FG_DIM': '#5f6368', 'FG_DARK': '#9aa0a6',
        'BORDER': '#c4c7c5', 'SUCCESS': '#188038', 'WARNING': '#e37400',
        'ERROR': '#d93025', 'SELECTION': '#a8c7fa',
    },
    'blue': {
        'BG': '#0d1117', 'BG_ALT': '#161b22', 'BG_HOVER': '#21262d',
        'FG': '#e6edf3', 'FG_DIM': '#8b949e', 'FG_DARK': '#484f58',
        'BORDER': '#30363d', 'SUCCESS': '#3fb950', 'WARNING': '#d29922',
        'ERROR': '#f85149', 'SELECTION': '#2f5496',
    },
}


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

    @classmethod
    def set(cls, name):
        for key, value in THEMES.get(name, THEMES['dark']).items():
            setattr(cls, key, value)

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
            QTableCornerButton::section {{ background-color: {Theme.BG_ALT}; border: 1px solid {Theme.BORDER}; }}
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

LANGS = {
    'ru': {
        'window_title': 'Proxy Switcher Pro v{v}',
        'app_title': 'Proxy Switcher Pro - v{v}',
        'grab': 'Собрать прокси',
        'verify': 'Проверить все',
        'del_dead': 'Удалить мертвые',
        'del_slow': 'Удалить медленные',
        'import': 'Импорт',
        'export': 'Экспорт',
        'rotate': 'Авторотация',
        'clear': 'Очистить все',
        'filter_placeholder': '🔍 Поиск: IP, страна, тип, статус...',
        'filter_alive_only': 'Только живые',
        'col_num': '№', 'col_ip': 'IP', 'col_port': 'ПОРТ', 'col_type': 'ТИП',
        'col_status': 'СТАТУС', 'col_speed': 'СКОРОСТЬ', 'col_anon': 'АНОНИМНОСТЬ', 'col_country': 'СТРАНА',
        'stats_fmt': 'Всего: {t} | Живых: {a} | Медленных: {s} | Мертвых: {d}',
        'offline': 'БЕЗ ПРОКСИ',
        'enabled_fmt': 'ВКЛЮЧЕН: {p}{speed}',
        'verified_fmt': 'ПРОВЕРЕНО: {a} живых | {d} мертвых',
        'disabled_btn': 'ПРОКСИ ВЫКЛЮЧЕН',
        'settings_title': 'Настройки',
        'settings_theme': 'Тема',
        'settings_lang': 'Язык',
        'settings_tray': 'Сворачивать в трей при закрытии',
        'settings_tooltip': 'Настройки (тема, язык)',
        'theme_dark': 'Тёмная',
        'theme_light': 'Светлая',
        'theme_blue': 'Синяя',
        'lang_ru': 'Русский',
        'lang_en': 'English',
        'save': 'СОХРАНИТЬ',
        'cancel': 'ОТМЕНА',
        'btn_collect': 'СОБРАТЬ',
        'btn_delete': 'Удалить',
        'q_title': 'Подтверждение',
        'done_title': 'Готово',
        'err_title': 'Ошибка',
        'info_title': 'Инфо',
        'success_title': 'Успех',
        'grab_title': 'Настройки сбора прокси',
        'grab_how_many': 'Сколько прокси собрать?',
        'grab_desc': 'Введите количество (10-500):\nИсточники опрашиваются параллельно',
        'grab_add': 'Добавить к существующим ({n})',
        'grab_confirm_add': 'Добавить {n} прокси?\n\nПараллельный сбор обычно занимает несколько секунд...',
        'grab_confirm_new': 'Собрать {n} прокси?\n\nПараллельный сбор обычно занимает несколько секунд...',
        'grab_done_text': 'Всего прокси: {n}\n\nСохранено: {f}\n\nТеперь нажми "Проверить все"!',
        'grab_fail_text': 'Не удалось собрать прокси\n\nПопробуй позже',
        'verify_empty': 'Нет прокси для проверки',
        'export_empty': 'Нет прокси для экспорта',
        'export_title': 'Экспорт прокси',
        'export_done': 'Экспортировано {n} прокси в:\n{f}',
        'del_dead_none': 'Нет мертвых прокси',
        'del_dead_confirm': 'Удалить {n} мертвых прокси?',
        'del_slow_title': 'Удалить медленные прокси',
        'del_slow_label': 'Удалить прокси медленнее (сек):',
        'del_slow_none': 'Нет прокси медленнее {t}s',
        'del_slow_confirm': 'Удалить {n} медленных прокси?',
        'import_title': 'Импорт прокси',
        'import_label': 'Введите прокси (по одному в строке):\nIP:PORT, socks5://IP:PORT, user:pass@IP:PORT',
        'import_done': 'Импортировано {n} прокси',
        'clear_confirm': 'Очистить ВСЕ прокси?',
        'win_only': 'Системная настройка прокси доступна только на Windows',
        'choose_proxy': 'Выберите прокси из таблицы',
        'only_working': 'Можно активировать только рабочие прокси (ALIVE или SLOW)\nТекущий: {s}',
        'proxy_on_text': 'Прокси включен\n{p}',
        'proxy_off_text': 'Прокси выключен\nПрямое соединение',
        'proxy_on_fail': 'Не удалось включить прокси: {e}',
        'proxy_off_fail': 'Не удалось выключить прокси: {e}',
        'rotate_title': 'Авторотация',
        'rotate_heading': 'Автоматическая ротация прокси',
        'rotate_enable': 'Включить авторотацию',
        'rotate_interval': 'Интервал (секунд):',
        'rotate_tip': 'Совет: используйте авторотацию для смены прокси каждые N секунд',
        'rotate_on_msg': 'Прокси будет меняться каждые {n} сек',
        'rotate_off_msg': 'Авторотация выключена',
        'tray_show': 'Показать окно',
        'tray_proxy_on': 'Включить прокси',
        'tray_proxy_off': 'Выключить прокси',
        'tray_exit': 'Выход',
        'tray_balloon': 'Программа свёрнута в трей — прокси продолжает работать.\nПолный выход: правый клик по значку → Выход.',
        'ctx_fav_add': '☆ Добавить в избранное',
        'ctx_fav_rem': '★ Убрать из избранного',
        'ctx_copy': '📋 Копировать IP:Port',
        'copied': 'Скопировано:\n{p}',
    },
    'en': {
        'window_title': 'Proxy Switcher Pro v{v}',
        'app_title': 'Proxy Switcher Pro - v{v}',
        'grab': 'Grab Proxies',
        'verify': 'Verify All',
        'del_dead': 'Delete Dead',
        'del_slow': 'Delete Slow',
        'import': 'Import',
        'export': 'Export',
        'rotate': 'Auto Rotate',
        'clear': 'Clear All',
        'filter_placeholder': '🔍 Search: IP, country, type, status...',
        'filter_alive_only': 'Alive only',
        'col_num': '#', 'col_ip': 'IP', 'col_port': 'PORT', 'col_type': 'TYPE',
        'col_status': 'STATUS', 'col_speed': 'SPEED', 'col_anon': 'ANONYMITY', 'col_country': 'COUNTRY',
        'stats_fmt': 'Total: {t} | Alive: {a} | Slow: {s} | Dead: {d}',
        'offline': 'OFFLINE',
        'enabled_fmt': 'ENABLED: {p}{speed}',
        'verified_fmt': 'VERIFIED: {a} alive | {d} dead',
        'disabled_btn': 'PROXY DISABLED',
        'settings_title': 'Settings',
        'settings_theme': 'Theme',
        'settings_lang': 'Language',
        'settings_tray': 'Minimize to tray on close',
        'settings_tooltip': 'Settings (theme, language)',
        'theme_dark': 'Dark',
        'theme_light': 'Light',
        'theme_blue': 'Blue',
        'lang_ru': 'Русский',
        'lang_en': 'English',
        'save': 'SAVE',
        'cancel': 'CANCEL',
        'btn_collect': 'COLLECT',
        'btn_delete': 'Delete',
        'q_title': 'Confirmation',
        'done_title': 'Done',
        'err_title': 'Error',
        'info_title': 'Info',
        'success_title': 'Success',
        'grab_title': 'Proxy grab settings',
        'grab_how_many': 'How many proxies to grab?',
        'grab_desc': 'Enter the amount (10-500):\nSources are fetched in parallel',
        'grab_add': 'Add to existing ({n})',
        'grab_confirm_add': 'Add {n} proxies?\n\nParallel grab usually takes a few seconds...',
        'grab_confirm_new': 'Grab {n} proxies?\n\nParallel grab usually takes a few seconds...',
        'grab_done_text': 'Total proxies: {n}\n\nSaved to: {f}\n\nNow press "Verify All"!',
        'grab_fail_text': 'Failed to grab proxies\n\nTry again later',
        'verify_empty': 'No proxies to check',
        'export_empty': 'No proxies to export',
        'export_title': 'Export proxies',
        'export_done': 'Exported {n} proxies to:\n{f}',
        'del_dead_none': 'No dead proxies',
        'del_dead_confirm': 'Delete {n} dead proxies?',
        'del_slow_title': 'Delete slow proxies',
        'del_slow_label': 'Delete proxies slower than (sec):',
        'del_slow_none': 'No proxies slower than {t}s',
        'del_slow_confirm': 'Delete {n} slow proxies?',
        'import_title': 'Import proxies',
        'import_label': 'Enter proxies (one per line):\nIP:PORT, socks5://IP:PORT, user:pass@IP:PORT',
        'import_done': 'Imported {n} proxies',
        'clear_confirm': 'Clear ALL proxies?',
        'win_only': 'System proxy configuration is only available on Windows',
        'choose_proxy': 'Select a proxy from the table',
        'only_working': 'Only working proxies can be activated (ALIVE or SLOW)\nCurrent: {s}',
        'proxy_on_text': 'Proxy enabled\n{p}',
        'proxy_off_text': 'Proxy disabled\nDirect connection',
        'proxy_on_fail': 'Failed to enable proxy: {e}',
        'proxy_off_fail': 'Failed to disable proxy: {e}',
        'rotate_title': 'Auto rotation',
        'rotate_heading': 'Automatic proxy rotation',
        'rotate_enable': 'Enable auto rotation',
        'rotate_interval': 'Interval (seconds):',
        'rotate_tip': 'Tip: use auto rotation to switch proxy every N seconds',
        'rotate_on_msg': 'Proxy will rotate every {n} sec',
        'rotate_off_msg': 'Auto rotation disabled',
        'tray_show': 'Show window',
        'tray_proxy_on': 'Enable proxy',
        'tray_proxy_off': 'Disable proxy',
        'tray_exit': 'Exit',
        'tray_balloon': 'The app is minimized to tray — the proxy keeps working.\nTo fully exit: right-click the tray icon → Exit.',
        'ctx_fav_add': '☆ Add to favorites',
        'ctx_fav_rem': '★ Remove from favorites',
        'ctx_copy': '📋 Copy IP:Port',
        'copied': 'Copied:\n{p}',
    },
}

_current_lang = 'ru'


def tr(key, **kwargs):
    s = LANGS.get(_current_lang, {}).get(key) or LANGS['en'].get(key) or key
    if kwargs:
        s = s.format(**kwargs)
    return s


PROXY_LINE_RE = re.compile(
    r'^(?:(?P<scheme>https?|socks4a?|socks5h?)://)?'
    r'(?:(?P<user>[^:@/\s]+):(?P<pass>[^@\s]+)@)?'
    r'(?P<ip>\d{1,3}(?:\.\d{1,3}){3}):(?P<port>\d{1,5})'
)

_COUNTRY_CACHE = {}


def is_valid_ip(ip):
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        return all(0 <= int(p) <= 255 for p in parts)
    except:
        return False


def parse_proxy_lines(text, default_type='HTTP'):
    """Построчный парсер: понимает префиксы протокола и user:pass@"""
    proxies = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = PROXY_LINE_RE.match(line)
        if not m:
            continue
        ptype = default_type
        scheme = m.group('scheme')
        if scheme:
            if scheme.startswith('socks5'):
                ptype = 'SOCKS5'
            elif scheme.startswith('socks4'):
                ptype = 'SOCKS4'
            elif scheme == 'https':
                ptype = 'HTTPS'
            else:
                ptype = 'HTTP'
        ip, port = m.group('ip'), m.group('port')
        if not is_valid_ip(ip) or not (1 <= int(port) <= 65535):
            continue
        proxies.append((ip, port, ptype, m.group('user') or '', m.group('pass') or ''))
    return proxies


def direct_proxies():
    """Пустой прокси-маппинг: без него requests подхватывает системный прокси из реестра
    Windows, и служебные запросы (сбор, гео, свой IP) шли бы через активный прокси"""
    return {'http': None, 'https': None}


JUDGES = [
    ('http://httpbin.org/ip', 'origin'),
    ('https://api.ipify.org?format=json', 'ip'),
    ('http://ip-api.com/json/?fields=query', 'query'),
]


def check_via_http(proxy_str, proxy_ip, timeout=3):
    """Проверка через HTTP-судей с фолбэком (httpbin бывает недоступен).
    Возвращает (status, speed, anonymity, error)"""
    pd = {'http': proxy_str, 'https': proxy_str}
    error = ''
    for url, field in JUDGES:
        start = time.time()
        try:
            r = requests.get(url, proxies=pd, timeout=timeout, headers={'User-Agent': 'Mozilla/5.0'})
            rt = time.time() - start
            if r.status_code == 200:
                try:
                    exit_ip = str(r.json().get(field, ''))
                except ValueError:
                    exit_ip = ''
                if exit_ip:
                    anonymity = 'transparent' if exit_ip == proxy_ip else 'elite'
                    return ('alive', round(rt, 2), anonymity, '')
                error = 'пустой ответ судьи'
            else:
                error = f'HTTP {r.status_code}'
        except requests.exceptions.Timeout:
            return ('slow', float(timeout), 'unknown', 'Timeout')
        except Exception as e:
            error = str(e)[:30]
    return ('dead', 0, 'unknown', error)


class ProxyGrabber(QThread):
    progress = pyqtSignal(int, str)
    proxy_found = pyqtSignal(str, str, str)
    finished = pyqtSignal(list)

    def __init__(self, max_proxies=100):
        super().__init__()
        self.max_proxies = max_proxies
        self._is_running = True
        self._lock = threading.Lock()
        self.found_proxies = []
        self.seen = set()
        logger.info(f"[GRABBER] Инициализирован (max={max_proxies})")

    def stop(self):
        if self._is_running:
            self._is_running = False
            logger.info("[GRABBER] Остановлен")

    def fetch_url(self, url, timeout=10):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        for attempt in (1, 2):
            try:
                r = requests.get(url, headers=headers, timeout=timeout, proxies=direct_proxies())
                r.raise_for_status()
                return r.text
            except requests.exceptions.Timeout:
                logger.warning(f"[TIMEOUT] {url}")
            except requests.exceptions.ConnectionError:
                logger.warning(f"[CONN_ERR] {url}")
            except Exception as e:
                logger.error(f"[FETCH_ERR] {url}: {e}")
                return None
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
                        if ip and port and is_valid_ip(ip) and port.isdigit():
                            proxies.append((ip, port))
                except:
                    continue
            return proxies
        except Exception as e:
            logger.error(f"[PARSE_ERR] {e}")
            return []

    def parse_json_proxies(self, text):
        """JSON-источники вида {"data": [{"ip": ..., "port": ..., "protocols": [...]}]}"""
        try:
            data = json.loads(text)
        except ValueError:
            return []
        items = data.get('data') if isinstance(data, dict) else data
        if not isinstance(items, list):
            return []
        proxies = []
        for item in items:
            if not isinstance(item, dict):
                continue
            ip = str(item.get('ip', '')).strip()
            port = str(item.get('port', '')).strip()
            if not is_valid_ip(ip) or not port.isdigit():
                continue
            protocols = item.get('protocols') or item.get('protocol') or []
            if isinstance(protocols, str):
                protocols = [protocols]
            ptype = 'HTTP'
            for p in protocols:
                ps = str(p).lower()
                if 'socks5' in ps:
                    ptype = 'SOCKS5'
                    break
                if 'socks4' in ps:
                    ptype = 'SOCKS4'
                    break
            proxies.append((ip, port, ptype, str(item.get('username') or ''), str(item.get('password') or '')))
        return proxies

    def add_proxy(self, ip, port, ptype='HTTP', login='', password=''):
        with self._lock:
            if len(self.found_proxies) >= self.max_proxies:
                self.stop()
                return False
            key = f"{ip}:{port}"
            if key in self.seen:
                return False
            self.seen.add(key)
            self.found_proxies.append({
                'ip': ip, 'port': port, 'type': ptype.upper(),
                'name': f"Proxy_{ip}", 'login': login, 'password': password,
                'status': 'fresh', 'speed': '', 'anonymity': 'unknown', 'country': '🌍',
            })
        self.proxy_found.emit(ip, port, ptype)
        return True

    def run(self):
        total = len(PROXY_SOURCES)
        logger.info(f"[GRABBER] Сбор из {total} источников (параллельно, {min(total, 6)} потоков)")
        completed = [0]

        def fetch_source(url, default_type):
            if not self._is_running:
                return None
            try:
                content = self.fetch_url(url)
                if not content:
                    return None
                stripped = content.lstrip()
                if stripped.startswith('{') or stripped.startswith('['):
                    return self.parse_json_proxies(content)
                if '<table' in content.lower():
                    return [(ip, port, default_type, '', '') for ip, port in self.parse_table_proxies(content)]
                return parse_proxy_lines(content, default_type)
            except Exception as e:
                logger.error(f"[SOURCE_ERR] {url}: {e}")
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(total, 6)) as executor:
            futures = [executor.submit(fetch_source, url, ptype) for url, ptype in PROXY_SOURCES]
            results = []
            for future in concurrent.futures.as_completed(futures):
                if not self._is_running:
                    break
                with self._lock:
                    completed[0] += 1
                    done = completed[0]
                self.progress.emit(int((done / total) * 100), f"Источники {done}/{total}")
                results.append(future.result())

        pool = [iter(lst) for lst in results if lst]
        while self._is_running and pool:
            alive_iterators = []
            for it in pool:
                try:
                    ip, port, ptype, login, password = next(it)
                    self.add_proxy(ip, port, ptype, login, password)
                    alive_iterators.append(it)
                except StopIteration:
                    pass
            pool = alive_iterators

        logger.info(f"[GRABBER] Собрано {len(self.found_proxies)} прокси")
        self.progress.emit(100, f"Готово: {len(self.found_proxies)} прокси")
        self.finished.emit(self.found_proxies)


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
        login = str(proxy.get('login') or '')
        password = str(proxy.get('password') or '')
        auth = f"{quote(login)}:{quote(password)}@" if login else ''

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

        if ptype in ['HTTP', 'HTTPS']:
            status, speed, anonymity, error = check_via_http(f"http://{auth}{ip}:{port}", ip)
            results['status'] = status
            results['speed'] = speed
            results['anonymity'] = anonymity
            results['error'] = error

        elif ptype in ['SOCKS4', 'SOCKS5']:
            if SOCKS_SUPPORTED:
                scheme = 'socks5' if ptype == 'SOCKS5' else 'socks4'
                status, speed, anonymity, error = check_via_http(f"{scheme}://{auth}{ip}:{port}", ip)
                results['status'] = status
                results['speed'] = speed
                results['anonymity'] = anonymity
                results['error'] = error
            else:

                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    start = time.time()
                    result = sock.connect_ex((ip, int(port)))
                    sock.close()
                    rt = time.time() - start
                    if result == 0:
                        results['status'] = 'slow'
                        results['speed'] = round(rt, 2)
                        results['error'] = 'port only (нет PySocks)'
                    else:
                        results['status'] = 'dead'
                except:
                    results['status'] = 'dead'

        return results

    def _resolve_countries(self):
        """Страны одним batch-запросом к ip-api.com (до 100 IP за запрос) вместо
        поштучных запросов, которые упираются в лимит 45 req/min и тормозят проверку"""
        unknown = []
        seen = set()
        for p in self.proxies:
            ip = p.get('ip', '')
            if ip and ip not in _COUNTRY_CACHE and ip not in seen:
                seen.add(ip)
                unknown.append(ip)
        if not unknown:
            return
        for start in range(0, len(unknown), 100):
            if not self._is_running:
                return
            chunk = unknown[start:start + 100]
            try:
                r = requests.post('http://ip-api.com/batch?fields=query,countryCode',
                                  json=[{'query': ip} for ip in chunk], timeout=15,
                                  headers={'User-Agent': 'Mozilla/5.0'},
                                  proxies=direct_proxies())
                if r.status_code != 200:
                    logger.warning(f"[GEO_ERR] batch HTTP {r.status_code}")
                    return
                for item in r.json():
                    ip = item.get('query', '')
                    cc = item.get('countryCode', '')
                    if ip and cc:
                        _COUNTRY_CACHE[ip] = cc
            except Exception as e:
                logger.warning(f"[GEO_ERR] batch: {e}")
                return
        for p in self.proxies:
            cc = _COUNTRY_CACHE.get(p.get('ip', ''))
            if cc:
                p['country'] = cc
        logger.info(f"[GEO] Определены страны: {len(_COUNTRY_CACHE)} IP в кэше")

    def run(self):
        total = len(self.proxies)
        logger.info(f"[CHECKER] Запуск проверки {total} прокси")

        try:
            r = requests.get('https://api.ipify.org?format=json', timeout=2, proxies=direct_proxies())
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

        self._resolve_countries()

        alive = sum(1 for p in self.proxies if p.get('status') == 'alive')
        slow = sum(1 for p in self.proxies if p.get('status') == 'slow')
        dead = sum(1 for p in self.proxies if p.get('status') == 'dead')
        logger.info(f"[CHECKER] Готово: {alive} живых | {slow} медленных | {dead} мертвых")

        self.finished.emit(self.proxies)


class ProxySwitcherPro(QMainWindow):
    ip_updated = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        logger.info(f"Инициализация {APP_NAME} v{VERSION}")

        self.proxies = []
        self.active_proxy = None
        self.proxy_enabled = False
        self.settings = self.default_settings()
        self.checker_thread = None
        self.grabber_thread = None
        self._really_quit = False
        self._tray_notified = False
        self.tray_icon = None

        try:
            self.load_settings()
            global _current_lang
            _current_lang = self.settings.get('lang', 'ru')
            Theme.set(self.settings.get('theme', 'dark'))
            self.init_ui()
            self.apply_theme()
            self.load_proxies()
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            raise

        self.ip_updated.connect(self._on_ip_updated)

        self.ip_timer = QTimer()
        self.ip_timer.timeout.connect(self.update_my_ip)
        self.ip_timer.start(15000)

        self.rotate_timer = QTimer()
        self.rotate_timer.timeout.connect(self.rotate_proxy)
        try:
            self.rotate_timer_interval = max(5, int(self.settings.get('rotate_interval', 60)))
        except (TypeError, ValueError):
            self.rotate_timer_interval = 60
        if self.settings.get('auto_rotate'):
            self.rotate_timer.start(self.rotate_timer_interval * 1000)
            logger.info(f"[ROTATE] Авторотация восстановлена: каждые {self.rotate_timer_interval} сек")

        self._init_tray()

        QTimer.singleShot(1000, self.update_my_ip)

    def default_settings(self):
        return {'theme': 'dark', 'lang': 'ru', 'timeout': 10, 'threads': 30,
                'auto_rotate': False, 'rotate_interval': 300, 'last_proxy': None,
                'minimize_to_tray': True}

    def init_ui(self):
        self.setWindowTitle(tr('window_title', v=VERSION))
        self.setGeometry(100, 100, 1200, 700)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        top = QHBoxLayout()
        self.title_label = QLabel(tr('app_title', v=VERSION))
        self.title_label.setObjectName("title")
        top.addWidget(self.title_label)
        top.addStretch()

        self.ip_label = QLabel("IP: ...")
        self.ip_label.setObjectName("subtitle")
        top.addWidget(self.ip_label)

        self._status_mode = 'offline'
        self._verified_counts = (0, 0)
        self.status_btn = QPushButton(tr('offline'))
        self.status_btn.setMaximumWidth(160)
        self.status_btn.clicked.connect(self.toggle_proxy)
        top.addWidget(self.status_btn)
        layout.addLayout(top)

        btns = QHBoxLayout()
        button_defs = [
            ('grab', self.grab_proxies),
            ('verify', self.check_all_proxies),
            ('del_dead', self.delete_dead_proxies),
            ('del_slow', self.delete_slow_proxies),
            ('import', self.import_proxies),
            ('export', self.export_proxies),
            ('rotate', self.setup_auto_rotate),
            ('clear', self.clear_all),
        ]
        self._action_buttons = []
        for key, cb in button_defs:
            btn = QPushButton(tr(key))
            btn.setMinimumWidth(100)
            btn.clicked.connect(cb)
            btns.addWidget(btn)
            self._action_buttons.append((btn, key))
        layout.addLayout(btns)

        filter_row = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText(tr('filter_placeholder'))
        self.filter_input.setClearButtonEnabled(True)
        self.filter_input.textChanged.connect(self.apply_filter)
        filter_row.addWidget(self.filter_input, 1)
        self.alive_only_cb = QCheckBox(tr('filter_alive_only'))
        self.alive_only_cb.toggled.connect(self.apply_filter)
        filter_row.addWidget(self.alive_only_cb)
        layout.addLayout(filter_row)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            tr('col_num'), tr('col_ip'), tr('col_port'), tr('col_type'),
            tr('col_status'), tr('col_speed'), tr('col_anon'), tr('col_country'),
        ])
        self.table.horizontalHeader().setStretchLastSection(True)

        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.itemDoubleClicked.connect(self.on_proxy_double_click)
        self.setup_table_context_menu()
        layout.addWidget(self.table)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(25)
        layout.addWidget(self.progress_bar)

        bottom = QHBoxLayout()
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(44, 32)
        self.settings_btn.setToolTip(tr('settings_tooltip'))
        self.settings_btn.clicked.connect(self.open_settings)
        bottom.addWidget(self.settings_btn)
        bottom.addSpacing(8)

        self.stats_label = QLabel(tr('stats_fmt', t=0, a=0, s=0, d=0))
        self.stats_label.setObjectName("stats")
        bottom.addWidget(self.stats_label, 1)
        layout.addLayout(bottom)

    def apply_theme(self):
        self.setStyleSheet(Theme.stylesheet())

    def open_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(tr('settings_title'))
        dialog.setStyleSheet(Theme.stylesheet())
        dialog.setFixedWidth(380)
        layout = QVBoxLayout(dialog)

        theme_label = QLabel(tr('settings_theme'))
        theme_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(theme_label)

        theme_combo = QComboBox()
        theme_keys = list(THEMES.keys())
        theme_combo.addItems([tr(f'theme_{k}') for k in theme_keys])
        cur_theme = self.settings.get('theme', 'dark')
        if cur_theme in theme_keys:
            theme_combo.setCurrentIndex(theme_keys.index(cur_theme))
        layout.addWidget(theme_combo)

        layout.addSpacing(10)

        lang_label = QLabel(tr('settings_lang'))
        lang_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(lang_label)

        lang_combo = QComboBox()
        lang_keys = list(LANGS.keys())

        lang_combo.addItems(['Русский' if k == 'ru' else 'English' for k in lang_keys])
        cur_lang = self.settings.get('lang', 'ru')
        if cur_lang in lang_keys:
            lang_combo.setCurrentIndex(lang_keys.index(cur_lang))
        layout.addWidget(lang_combo)

        layout.addSpacing(10)

        tray_checkbox = QCheckBox(tr('settings_tray'))
        tray_checkbox.setChecked(self.settings.get('minimize_to_tray', True))
        layout.addWidget(tray_checkbox)

        layout.addSpacing(15)

        btns = QHBoxLayout()
        ok_btn = QPushButton(tr('save'))
        ok_btn.setObjectName("primary")
        cancel_btn = QPushButton(tr('cancel'))
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        def save_settings():
            new_theme = theme_keys[theme_combo.currentIndex()]
            new_lang = lang_keys[lang_combo.currentIndex()]

            self.settings['theme'] = new_theme
            self.settings['lang'] = new_lang
            self.settings['minimize_to_tray'] = tray_checkbox.isChecked()

            global _current_lang
            _current_lang = new_lang
            Theme.set(new_theme)

            self.apply_theme()
            self.retranslate_ui()
            self.refresh_table()
            self.update_status_btn()
            self.save_settings()
            dialog.accept()

        ok_btn.clicked.connect(save_settings)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec_()

    def retranslate_ui(self):
        """Обновить все тексты интерфейса после смены языка"""
        self.setWindowTitle(tr('window_title', v=VERSION))
        self.title_label.setText(tr('app_title', v=VERSION))
        for btn, key in self._action_buttons:
            btn.setText(tr(key))
        self.table.setHorizontalHeaderLabels([
            tr('col_num'), tr('col_ip'), tr('col_port'), tr('col_type'),
            tr('col_status'), tr('col_speed'), tr('col_anon'), tr('col_country'),
        ])
        self.settings_btn.setToolTip(tr('settings_tooltip'))
        self.filter_input.setPlaceholderText(tr('filter_placeholder'))
        self.alive_only_cb.setText(tr('filter_alive_only'))
        if self.tray_icon is not None:
            self.tray_show_action.setText(tr('tray_show'))
            self.tray_exit_action.setText(tr('tray_exit'))
            self.update_status_btn()
        self._update_stats()

    def update_status_btn(self):
        """Перерисовать кнопку статуса (текст + цвет) по текущему состоянию"""
        if (self._status_mode == 'enabled' and self.proxy_enabled
                and self.active_proxy is not None and self.active_proxy < len(self.proxies)):
            proxy = self.proxies[self.active_proxy]
            emoji = "🟢" if proxy.get('status') == 'alive' else "🟡"
            speed_info = f" ({proxy.get('speed', '?')}s)" if proxy.get('speed') else ""
            self.status_btn.setText(f"{emoji} " + tr('enabled_fmt', p=f"{proxy['ip']}:{proxy['port']}", speed=speed_info))
            self.status_btn.setStyleSheet(f"""
                QPushButton {{ background-color: {Theme.SUCCESS}; color: white; border: none; border-radius: 4px; padding: 8px 16px; font-weight: bold; }}
                QPushButton:hover {{ background-color: #388e3c; }}
            """)
        elif self._status_mode == 'disabled':
            self.status_btn.setText(tr('disabled_btn'))
            self.status_btn.setStyleSheet(f"""
                QPushButton {{ background-color: {Theme.ERROR}; color: white; border: none; border-radius: 4px; padding: 8px 16px; font-weight: bold; }}
                QPushButton:hover {{ background-color: #d32f2f; }}
            """)
        elif self._status_mode == 'verified':
            a, d = self._verified_counts
            self.status_btn.setText(tr('verified_fmt', a=a, d=d))
            self.status_btn.setStyleSheet('')
        else:
            self.status_btn.setText(tr('offline'))
            self.status_btn.setStyleSheet('')

        if self.tray_icon is not None:
            self.tray_toggle_action.setText(tr('tray_proxy_off') if self.proxy_enabled else tr('tray_proxy_on'))
            self.tray_icon.setToolTip(f"{APP_NAME} v{VERSION}\n{self.status_btn.text()}")

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
        self.apply_filter()

    def apply_filter(self):
        """Скрыть строки, не подходящие под поисковый запрос и галочку «только живые»"""
        if not hasattr(self, 'filter_input'):
            return
        text = self.filter_input.text().strip().lower()
        only_alive = self.alive_only_cb.isChecked()
        for row, proxy in enumerate(self.proxies):
            if only_alive and proxy.get('status') != 'alive':
                self.table.setRowHidden(row, True)
                continue
            if not text:
                self.table.setRowHidden(row, False)
                continue
            hay = ' '.join(str(proxy.get(k, '')) for k in ('ip', 'port', 'type', 'status', 'country', 'anonymity')).lower()
            self.table.setRowHidden(row, text not in hay)

    def _update_stats(self):
        total = len(self.proxies)
        alive = sum(1 for p in self.proxies if p.get('status') == 'alive')
        slow = sum(1 for p in self.proxies if p.get('status') == 'slow')
        dead = sum(1 for p in self.proxies if p.get('status') == 'dead')
        self.stats_label.setText(tr('stats_fmt', t=total, a=alive, s=slow, d=dead))

    def grab_proxies(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(tr('grab_title'))
        dialog.setStyleSheet(Theme.stylesheet())
        layout = QVBoxLayout(dialog)

        title = QLabel(tr('grab_how_many'))
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)

        desc = QLabel(tr('grab_desc'))
        desc.setFont(QFont("Segoe UI", 10))
        desc.setStyleSheet(f"color: {Theme.FG_DIM};")
        layout.addWidget(desc)

        spinbox = QSpinBox()
        spinbox.setRange(10, 500)
        spinbox.setValue(100)
        spinbox.setSingleStep(10)
        spinbox.setMinimumHeight(40)
        layout.addWidget(spinbox)

        add_checkbox = QCheckBox(tr('grab_add', n=len(self.proxies)))
        add_checkbox.setChecked(len(self.proxies) > 0)
        layout.addWidget(add_checkbox)

        btns = QHBoxLayout()
        ok_btn = QPushButton(tr('btn_collect'))
        ok_btn.setObjectName("primary")
        cancel_btn = QPushButton(tr('cancel'))
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        if dialog.exec_() != QDialog.Accepted:
            return

        count = spinbox.value()
        add_to_existing = add_checkbox.isChecked()

        confirm_key = 'grab_confirm_add' if add_to_existing else 'grab_confirm_new'
        reply = QMessageBox.question(self, tr('q_title'),
            tr(confirm_key, n=count),
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
            QMessageBox.information(self, tr('done_title'),
                tr('grab_done_text', n=total, f=str(CONFIG_FILE)))
        else:
            QMessageBox.warning(self, tr('err_title'), tr('grab_fail_text'))

    def check_all_proxies(self):
        if not self.proxies:
            QMessageBox.warning(self, tr('err_title'), tr('verify_empty'))
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

            ip_item = self.table.item(index, 1)
            if ip_item is not None:
                if status == 'alive':
                    ip_item.setForeground(QColor(Theme.SUCCESS))
                elif status == 'dead':
                    ip_item.setForeground(QColor(Theme.ERROR))
                elif status == 'slow':
                    ip_item.setForeground(QColor(Theme.WARNING))
                else:
                    ip_item.setForeground(QColor(Theme.FG))

            speed = result.get('speed', '')
            speed_item = QTableWidgetItem(f"{speed}s" if speed else "-")
            self.table.setItem(index, 5, speed_item)

            anon = result.get('anonymity', 'unknown')
            anon_emoji = '🟢' if anon == 'elite' else '🟡' if anon == 'anonymous' else '🔴'
            anon_item = QTableWidgetItem(f"{anon_emoji} {anon}")
            anon_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(index, 6, anon_item)

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
        self._verified_counts = (alive, dead)
        if not self.proxy_enabled:
            self._status_mode = 'verified'
            self.update_status_btn()

    def delete_dead_proxies(self):
        dead = [p for p in self.proxies if p.get('status') == 'dead']
        if not dead:
            QMessageBox.information(self, tr('info_title'), tr('del_dead_none'))
            return

        reply = QMessageBox.question(self, tr('q_title'), tr('del_dead_confirm', n=len(dead)), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.proxies = [p for p in self.proxies if p.get('status') != 'dead']
            self.refresh_table()
            self.save_proxies()

    def delete_slow_proxies(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(tr('del_slow_title'))
        dialog.setStyleSheet(Theme.stylesheet())
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel(tr('del_slow_label')))
        speed_spin = QDoubleSpinBox()
        speed_spin.setRange(0.1, 60.0)
        speed_spin.setValue(2.0)
        layout.addWidget(speed_spin)

        btns = QHBoxLayout()
        ok_btn = QPushButton(tr('btn_delete'))
        ok_btn.setObjectName("danger")
        cancel_btn = QPushButton(tr('cancel'))
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
            QMessageBox.information(self, tr('info_title'), tr('del_slow_none', t=threshold))
            return

        reply = QMessageBox.question(self, tr('q_title'), tr('del_slow_confirm', n=len(slow)), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.proxies = [p for p in self.proxies if not (p.get('speed', 0) and float(p.get('speed', 0)) > threshold)]
            self.refresh_table()
            self.save_proxies()

    def import_proxies(self):
        text, ok = QInputDialog.getMultiLineText(self, tr('import_title'), tr('import_label'))
        if not ok or not text.strip():
            return

        existing = {f"{p.get('ip')}:{p.get('port')}" for p in self.proxies}
        added = 0
        for ip, port, ptype, login, password in parse_proxy_lines(text, 'HTTP'):
            key = f"{ip}:{port}"
            if key in existing:
                continue
            existing.add(key)
            self.proxies.append({'ip': ip, 'port': port, 'type': ptype, 'name': f"Proxy_{ip}",
                                 'login': login, 'password': password,
                                 'status': 'fresh', 'speed': '', 'anonymity': 'unknown', 'country': '🌍'})
            added += 1

        self.refresh_table()
        self.save_proxies()
        QMessageBox.information(self, tr('success_title'), tr('import_done', n=added))

    def export_proxies(self):
        if not self.proxies:
            QMessageBox.warning(self, tr('err_title'), tr('export_empty'))
            return

        default_path = Path.home() / 'Desktop' / 'proxies.txt'
        path, _ = QFileDialog.getSaveFileName(self, tr('export_title'), str(default_path), 'Text files (*.txt)')
        if not path:
            return

        lines = []
        for p in self.proxies:
            addr = f"{p.get('ip')}:{p.get('port')}"
            login = str(p.get('login') or '')
            if login:
                addr = f"{login}:{p.get('password') or ''}@{addr}"
            ptype = str(p.get('type', 'HTTP')).upper()
            if ptype.startswith('SOCKS'):
                addr = f"{ptype.lower()}://{addr}"
            lines.append(addr)

        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines) + '\n')
            QMessageBox.information(self, tr('success_title'), tr('export_done', n=len(lines), f=path))
        except Exception as e:
            logger.error(f"[EXPORT_ERR] {e}")
            QMessageBox.critical(self, tr('err_title'), str(e))

    def clear_all(self):
        reply = QMessageBox.question(self, tr('q_title'), tr('clear_confirm'), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.proxies = []
            self.refresh_table()
            self.save_proxies()

    def on_proxy_double_click(self, item):
        """Двойной клик по прокси - включить/выключить"""
        row = item.row()
        if row < 0 or row >= len(self.proxies):
            return

        if self.proxy_enabled and self.active_proxy == row:
            self.disable_proxy()
        else:
            self.table.setCurrentCell(row, 0)
            self.enable_proxy()

    def toggle_proxy(self):
        if self.proxy_enabled:
            self.disable_proxy()
        else:
            self.enable_proxy()

    def enable_proxy(self, silent=False):
        if not IS_WINDOWS:
            QMessageBox.warning(self, tr('err_title'), tr('win_only'))
            return

        row = self.table.currentRow()
        if row < 0 or row >= len(self.proxies):
            QMessageBox.warning(self, tr('err_title'), tr('choose_proxy'))
            return

        proxy = self.proxies[row]
        if proxy.get('status') not in ['alive', 'slow']:
            QMessageBox.warning(self, tr('err_title'), tr('only_working', s=str(proxy.get('status', 'unknown')).upper()))
            return

        try:
            import winreg
            import ctypes
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)

            if proxy.get('type', 'HTTP').upper().startswith('SOCKS'):
                proxy_server = f"socks={proxy['ip']}:{proxy['port']}"
            else:
                proxy_server = f"{proxy['ip']}:{proxy['port']}"
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy_server)

            # Локальные адреса мимо прокси; прежний список исключений сохраняем и вернём при выключении
            try:
                prev_override = winreg.QueryValueEx(key, "ProxyOverride")[0]
            except OSError:
                prev_override = ""
            if prev_override != PROXY_OVERRIDE:
                self.settings['proxy_override_backup'] = prev_override
            winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, PROXY_OVERRIDE)
            winreg.CloseKey(key)

            # 39 - уведомить приложения о смене настроек, 37 - применить их сразу
            ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
            ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)

            self.proxy_enabled = True
            self.active_proxy = row
            self.settings['last_proxy'] = row
            self.save_settings()
            self._status_mode = 'enabled'
            self.update_status_btn()
            if not silent:
                QMessageBox.information(self, tr('success_title'), tr('proxy_on_text', p=f"{proxy['ip']}:{proxy['port']}"))
        except Exception as e:
            logger.error(f"[PROXY_ON] {e}")
            if not silent:
                QMessageBox.critical(self, tr('err_title'), tr('proxy_on_fail', e=e))

    def disable_proxy(self, silent=False):
        if not IS_WINDOWS:
            QMessageBox.warning(self, tr('err_title'), tr('win_only'))
            return

        try:
            import winreg
            import ctypes
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_SET_VALUE)
            backup = self.settings.pop('proxy_override_backup', None)
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "")
            if backup is not None:
                winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, backup)
            winreg.CloseKey(key)
            ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
            ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)

            self.proxy_enabled = False
            self.active_proxy = None
            self.save_settings()
            self._status_mode = 'disabled'
            self.update_status_btn()
            if not silent:
                QMessageBox.information(self, tr('success_title'), tr('proxy_off_text'))
        except Exception as e:
            logger.error(f"[PROXY_OFF] {e}")
            if not silent:
                QMessageBox.critical(self, tr('err_title'), tr('proxy_off_fail', e=e))

    def rotate_proxy(self):
        if not self.proxy_enabled:
            return

        candidates = [i for i, p in enumerate(self.proxies) if p.get('status') == 'alive']
        if not candidates:
            candidates = [i for i, p in enumerate(self.proxies) if p.get('status') == 'slow']
        if not candidates:
            logger.warning("[ROTATE] Нет живых прокси для ротации")
            return

        candidates = [i for i in candidates if i != self.active_proxy] or candidates

        next_idx = random.choice(candidates)
        self.disable_proxy(silent=True)
        self.table.setCurrentCell(next_idx, 0)
        self.enable_proxy(silent=True)

    def setup_auto_rotate(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(tr('rotate_title'))
        dialog.setStyleSheet(Theme.stylesheet())
        layout = QVBoxLayout(dialog)

        title = QLabel(tr('rotate_heading'))
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)

        enable_checkbox = QCheckBox(tr('rotate_enable'))
        enable_checkbox.setChecked(self.settings.get('auto_rotate', False))
        layout.addWidget(enable_checkbox)

        layout.addWidget(QLabel(tr('rotate_interval')))
        interval_spin = QSpinBox()
        interval_spin.setRange(5, 3600)
        interval_spin.setValue(self.rotate_timer_interval)
        interval_spin.setSingleStep(5)
        interval_spin.setMinimumHeight(36)
        layout.addWidget(interval_spin)

        layout.addSpacing(15)
        layout.addWidget(QLabel(tr('rotate_tip')))

        btns = QHBoxLayout()
        ok_btn = QPushButton(tr('save'))
        ok_btn.setObjectName("primary")
        cancel_btn = QPushButton(tr('cancel'))
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        def save_settings():
            enabled = enable_checkbox.isChecked()
            interval = interval_spin.value()

            self.settings['auto_rotate'] = enabled
            self.settings['rotate_interval'] = interval
            self.rotate_timer_interval = interval
            self.save_settings()

            if enabled:
                self.rotate_timer.start(interval * 1000)
                QMessageBox.information(self, tr('rotate_title'), tr('rotate_on_msg', n=interval))
            else:
                self.rotate_timer.stop()
                QMessageBox.information(self, tr('rotate_title'), tr('rotate_off_msg'))

            dialog.accept()

        ok_btn.clicked.connect(save_settings)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec_()

    def update_my_ip(self):
        def check_ip():
            try:
                # Намеренно без direct_proxies(): индикатор показывает IP, который видит интернет,
                # т.е. exit IP при включённом системном прокси и реальный при выключенном
                r = requests.get('https://api.ipify.org?format=json', timeout=3)
                ip = r.json().get('ip', 'Unknown')
                self.ip_updated.emit(ip)
            except:
                self.ip_updated.emit('Unknown')

        threading.Thread(target=check_ip, daemon=True).start()

    def _on_ip_updated(self, ip):
        self.ip_label.setText(f"IP: {ip}")

    def closeEvent(self, event):
        if (self.tray_icon is not None and self.settings.get('minimize_to_tray', True)
                and not self._really_quit):
            event.ignore()
            self.hide()
            if not self._tray_notified:
                self._tray_notified = True
                self.tray_icon.showMessage(APP_NAME, tr('tray_balloon'), QSystemTrayIcon.Information, 4000)
            return

        logger.info("Закрытие приложения, сохранение данных...")
        try:
            if self.grabber_thread is not None and self.grabber_thread.isRunning():
                self.grabber_thread.stop()
            if self.checker_thread is not None and self.checker_thread.isRunning():
                self.checker_thread.stop()
            if self.tray_icon is not None:
                self.tray_icon.hide()
            self.save_proxies()
            self.save_settings()
        except Exception as e:
            logger.error(f"Ошибка при закрытии: {e}")
        event.accept()

    def _create_app_icon(self):
        """Иконка рисуется программно (круг + стрелки обмена), без внешних файлов"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor('#4caf50'))
        p.setPen(QPen(QColor('#2e7d32'), 3))
        p.drawEllipse(4, 4, 56, 56)
        p.setPen(QPen(QColor('#ffffff'), 5, Qt.SolidLine, Qt.RoundCap, Qt.MiterJoin))
        p.drawLine(20, 25, 44, 25)
        p.drawLine(44, 25, 37, 18)
        p.drawLine(44, 25, 37, 32)
        p.drawLine(44, 41, 20, 41)
        p.drawLine(20, 41, 27, 34)
        p.drawLine(20, 41, 27, 48)
        p.end()
        return QIcon(pixmap)

    def _init_tray(self):
        icon = self._create_app_icon()
        self.setWindowIcon(icon)
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.info("[TRAY] Системный трей недоступен")
            return

        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_menu = QMenu()
        menu = self.tray_menu
        self.tray_show_action = menu.addAction(tr('tray_show'))
        self.tray_show_action.triggered.connect(self.show_and_raise)
        menu.addSeparator()
        self.tray_toggle_action = menu.addAction(tr('tray_proxy_on'))
        self.tray_toggle_action.triggered.connect(self.toggle_proxy)
        menu.addSeparator()
        self.tray_exit_action = menu.addAction(tr('tray_exit'))
        self.tray_exit_action.triggered.connect(self.quit_from_tray)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.setToolTip(f"{APP_NAME} v{VERSION}")
        self.tray_icon.show()
        self.update_status_btn()

    def show_and_raise(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def quit_from_tray(self):
        self._really_quit = True
        self.close()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_and_raise()

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
            action = menu.addAction(tr('ctx_fav_rem'))
        else:
            action = menu.addAction(tr('ctx_fav_add'))
        action.triggered.connect(lambda: self.toggle_favorite(index))

        menu.addSeparator()

        copy_action = menu.addAction(tr('ctx_copy'))
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
        QMessageBox.information(self, tr('success_title'), tr('copied', p=proxy_str))


def main():
    app = QApplication(sys.argv)
    window = ProxySwitcherPro()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
