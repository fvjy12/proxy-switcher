# Proxy Switcher Pro

Инструмент для управления прокси: сбор из 14 источников, проверка, применение на уровне системы Windows.


## Возможности

- Сбор прокси из 14 источников (HTTP, SOCKS4, SOCKS5)
- Параллельная проверка прокси (ThreadPoolExecutor)
- Определение анонимности (elite, anonymous, transparent)
- Определение страны по IP
- Применение прокси на уровне Windows (реестр)
- Авторотация прокси по таймеру
- Избранное и копирование в буфер обмена
- Чёрно-белый дизайн

## Источники прокси

Программа собирает прокси из 14 источников, включая:

- [free-proxy-list.net](https://free-proxy-list.net) - бесплатные прокси
- [ProxyScrape](https://proxyscrape.com) - API прокси
- [GitHub proxy lists](https://github.com/TheSpeedX/PROXY-List) - открытые списки
- [sslproxies.org](https://www.sslproxies.org) - SSL прокси
- и другие

Также можно импортировать свои прокси через кнопку **Import**.


## Установка

```bash
pip install -r requirements.txt
```

## Запуск

```bash
python proxy_switcher.py
```

## Кнопки

| Кнопка | Что делает |
|--------|-----------|
| Grab Proxies | Собрать прокси из всех источников |
| Verify All | Проверить все прокси |
| Delete Dead | Удалить нерабочие |
| Delete Slow | Удалить медленные |
| Import | Импорт своих прокси |
| Auto Rotate | Авторотация |
| Clear All | Очистить всё |

## Файлы

- `proxy_switcher.py` - основное приложение
- `import.py` - модуль импорта прокси
- `requirements.txt` - зависимости

## Настройки

Данные хранятся в `~/Documents/ProxySwitcher/`:
- `proxies.json` - список прокси
- `settings.json` - настройки
- `logs/` - логи

## Платформы

- Windows - полная поддержка (включая системный прокси)
- Linux/macOS - GUI работает, системный прокси недоступен

## Лицензия

MIT
