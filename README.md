# Agro Tools

Полевой помощник агронома на Python с интерфейсом Kivy и сборкой для Android.

## Возможности

- Расчёт нормы высева.
- Расчёт опрыскивания и заправок.
- Карточки полей и журнал работ.
- Сохранение расчёта опрыскивания в историю поля.
- Локальное хранение данных в SQLite.

## Разработка

Рабочая среда: Ubuntu в WSL2, VS Code и uv.

Проект следует размещать внутри файловой системы Linux,
например в ~/projects/agro-tools-unified.

### Подготовка Python-окружения

Из папки проекта:

```bash
uv sync --locked --python /usr/bin/python3
```

Для Android-сборки используется Python 3.14.
Версия Buildozer закреплена в pyproject.toml и uv.lock.

### Тесты

```bash
uv run pytest -q
```

### Запуск интерфейса на компьютере

Для интерфейса используется отдельное окружение:
Python 3.13 и Kivy 2.3.1.

```bash
uv run --no-project --python 3.13 --with "kivy==2.3.1" python main.py
```

Для запуска в WSL требуется поддержка графических приложений WSLg.

При отсутствии компонентов сенсорного ввода и буфера обмена:

```bash
sudo apt install -y libmtdev1 xclip xsel
```

## Сборка Android

Помимо Python-окружения требуются Java 17, Rust
и системные зависимости Buildozer.

Инструкция установки:
https://github.com/kivy/buildozer/blob/master/docs/source/installation.rst

Настройки сборки находятся в buildozer.spec.

```bash
uv run buildozer -v android debug
```

Готовый APK появляется в папке bin/.
Текущая архитектура: arm64-v8a.

## Структура

- main.py — мобильный интерфейс и запуск приложения.
- src/agro_tools/ — расчёты, хранение данных и экраны полей.
- tests/ — тесты.
- buildozer.spec — настройки Android.
- pyproject.toml и uv.lock — зависимости Python.
- AGRO_TOOLS_CONCEPT.md — концепция проекта.

## Данные

SQLite-база хранится в каталоге данных приложения.
Данные на компьютере и телефоне независимы.

База, APK, окружения и кеши сборки не сохраняются в Git.
Удаление приложения или очистка его данных может удалить журнал.