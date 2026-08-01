#!/usr/bin/env python3
"""
Proxy Switcher Pro - Import Module
Version 2.0.0

This module provides functions for importing proxies from various sources:
- Text files (IP:PORT format)
- JSON files
- CSV files
- URLs
"""

import re
import json
import csv
from pathlib import Path
from typing import List, Dict, Optional

import requests


def parse_proxy_line(line: str) -> Optional[Dict]:
    """Parse a single proxy line in IP:PORT format"""
    line = line.strip()
    if not line:
        return None

    # Match IP:PORT
    pattern = r'(\d+\.\d+\.\d+\.\d+):(\d+)'
    match = re.search(pattern, line)
    if not match:
        return None

    ip, port = match.groups()

    # Determine proxy type
    proxy_type = 'HTTP'
    line_lower = line.lower()
    if 'socks5' in line_lower:
        proxy_type = 'SOCKS5'
    elif 'socks4' in line_lower:
        proxy_type = 'SOCKS4'
    elif 'https' in line_lower:
        proxy_type = 'HTTPS'

    return {
        'ip': ip,
        'port': port,
        'type': proxy_type,
        'name': f"Proxy_{ip}",
        'login': '',
        'password': '',
        'status': 'fresh',
        'speed': '',
        'anonymity': 'unknown',
        'country': '🌍',
    }


def import_from_text(text: str) -> List[Dict]:
    """Import proxies from raw text"""
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


def import_from_file(filepath: str) -> List[Dict]:
    """Import proxies from a file (txt, json, csv)"""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    suffix = path.suffix.lower()

    if suffix == '.json':
        return import_from_json(path)
    elif suffix == '.csv':
        return import_from_csv(path)
    else:
        # Default to text
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return import_from_text(f.read())


def import_from_json(path: Path) -> List[Dict]:
    """Import proxies from JSON file"""
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
                        proxy = {
                            'ip': ip,
                            'port': str(port),
                            'type': item.get('type', 'HTTP'),
                            'name': item.get('name', f"Proxy_{ip}"),
                            'login': item.get('login', ''),
                            'password': item.get('password', ''),
                            'status': item.get('status', 'fresh'),
                            'speed': item.get('speed', ''),
                            'anonymity': item.get('anonymity', 'unknown'),
                            'country': item.get('country', '🌍'),
                        }
                        proxies.append(proxy)
            elif isinstance(item, str):
                proxy = parse_proxy_line(item)
                if proxy:
                    key = f"{proxy['ip']}:{proxy['port']}"
                    if key not in seen:
                        seen.add(key)
                        proxies.append(proxy)

    return proxies


def import_from_csv(path: Path) -> List[Dict]:
    """Import proxies from CSV file"""
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
                        proxy_type = row[2].strip().upper() if len(row) > 2 else 'HTTP'
                        proxies.append({
                            'ip': ip,
                            'port': port,
                            'type': proxy_type,
                            'name': f"Proxy_{ip}",
                            'login': '',
                            'password': '',
                            'status': 'fresh',
                            'speed': '',
                            'anonymity': 'unknown',
                            'country': '🌍',
                        })

    return proxies


def import_from_url(url: str, timeout: int = 10) -> List[Dict]:
    """Import proxies from a URL"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return import_from_text(response.text)


def merge_proxies(existing: List[Dict], new: List[Dict]) -> List[Dict]:
    """Merge two proxy lists, removing duplicates"""
    seen = set()
    result = []

    for proxy in existing + new:
        key = f"{proxy.get('ip')}:{proxy.get('port')}"
        if key not in seen:
            seen.add(key)
            result.append(proxy)

    return result


if __name__ == "__main__":
    # Example usage
    sample = "192.168.1.1:8080\n10.0.0.1:3128\n"
    proxies = import_from_text(sample)
    print(f"Imported {len(proxies)} proxies:")
    for p in proxies:
        print(f"  {p['ip']}:{p['port']} ({p['type']})")
