#!/usr/bin/env python3
# Модуль импорта прокси для Proxy Switcher Pro

import re
import json
import csv
from pathlib import Path

import requests


def parse_proxy_line(line):
    """Разбирает строку вида IP:PORT"""
    line = line.strip()
    if not line:
        return None

    pattern = r'(\d+\.\d+\.\d+\.\d+):(\d+)'
    match = re.search(pattern, line)
    if not match:
        return None

    ip, port = match.groups()

    # определяем тип
    ptype = 'HTTP'
    low = line.lower()
    if 'socks5' in low:
        ptype = 'SOCKS5'
    elif 'socks4' in low:
        ptype = 'SOCKS4'
    elif 'https' in low:
        ptype = 'HTTPS'

    return {
        'ip': ip, 'port': port, 'type': ptype,
        'name': f"Proxy_{ip}", 'login': '', 'password': '',
        'status': 'fresh', 'speed': '', 'anonymity': 'unknown', 'country': '🌍',
    }


def import_from_text(text):
    """Импорт из текста"""
    proxies = []
    seen = set()

    for line in text.splitlines():
        proxy = parse_proxy_line(line)
        if proxy:
            key = f"{proxy['ip']}:{proxy['port']}"
            if key not in seen:
                seen.add(key)
                proxies.append(proxy)

    return proxies


def import_from_file(filepath):
    """Импорт из файла (txt, json, csv)"""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {filepath}")

    suffix = path.suffix.lower()

    if suffix == '.json':
        return import_from_json(path)
    elif suffix == '.csv':
        return import_from_csv(path)
    else:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return import_from_text(f.read())


def import_from_json(path):
    """Импорт из JSON"""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    proxies = []
    seen = set()

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                ip = item.get('ip', '')
                port = item.get('port', '')
                if ip and port:
                    key = f"{ip}:{port}"
                    if key not in seen:
                        seen.add(key)
                        proxies.append({
                            'ip': ip, 'port': str(port),
                            'type': item.get('type', 'HTTP'),
                            'name': item.get('name', f"Proxy_{ip}"),
                            'login': item.get('login', ''),
                            'password': item.get('password', ''),
                            'status': item.get('status', 'fresh'),
                            'speed': item.get('speed', ''),
                            'anonymity': item.get('anonymity', 'unknown'),
                            'country': item.get('country', '🌍'),
                        })
            elif isinstance(item, str):
                proxy = parse_proxy_line(item)
                if proxy:
                    key = f"{proxy['ip']}:{proxy['port']}"
                    if key not in seen:
                        seen.add(key)
                        proxies.append(proxy)

    return proxies


def import_from_csv(path):
    """Импорт из CSV"""
    proxies = []
    seen = set()

    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                ip = row[0].strip()
                port = row[1].strip()
                if ip and port:
                    key = f"{ip}:{port}"
                    if key not in seen:
                        seen.add(key)
                        ptype = row[2].strip().upper() if len(row) > 2 else 'HTTP'
                        proxies.append({
                            'ip': ip, 'port': port, 'type': ptype,
                            'name': f"Proxy_{ip}", 'login': '', 'password': '',
                            'status': 'fresh', 'speed': '', 'anonymity': 'unknown', 'country': '🌍',
                        })

    return proxies


def import_from_url(url, timeout=10):
    """Импорт с URL"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return import_from_text(r.text)


def merge_proxies(existing, new):
    """Объединяет два списка прокси, убирая дубликаты"""
    seen = set()
    result = []

    for proxy in existing + new:
        key = f"{proxy.get('ip')}:{proxy.get('port')}"
        if key not in seen:
            seen.add(key)
            result.append(proxy)

    return result


if __name__ == "__main__":
    sample = "192.168.1.1:8080\n10.0.0.1:3128\n"
    proxies = import_from_text(sample)
    print(f"Импортировано {len(proxies)} прокси:")
    for p in proxies:
        print(f"  {p['ip']}:{p['port']} ({p['type']})")
