# Turborand Dashboard

Веб-приложение на Flask, отображающее ключевые метрики работы отдела продаж и снабжения. Данные периодически выгружаются из CRM и других сервисов, обрабатываются и сохраняются во внутреннюю базу SQLite.

## Структура проекта
- `app.py` – запуск Flask-приложения и отдача актуальных данных на HTML‑шаблоны.
- `updater.py` – фоновой процесс, который раз в несколько минут обновляет данные, вызывая скрипты из каталога `updaters/`.
- `updaters/` – отдельные модули для загрузки пользователей, сделок, платежей, звонков и т.д.
- `db.py` – работа с внутренней базой SQLite.
- `init.py` – создание схемы базы из `schema.sql`.
- `templates/` и `static/` – шаблоны и статические файлы интерфейса.

## Требования
- Python 3.11+
- Доступ к основному MySQL‑серверу и внешним сервисам CRM
- Рекомендуется использовать виртуальное окружение и установить зависимости из `requirements.txt`

## Установка
1. **Клонирование репозитория**
   ```bash
   git clone https://example.com/turborand_dashboard.git
   cd turborand_dashboard
   ```
2. **Создание окружения и установка зависимостей**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Конфигурация**
   Создайте файл `.env` в корне проекта и укажите параметры подключения. Минимальный набор переменных:
   ```dotenv
   MYSQL_HOST=host
   MYSQL_PORT=3306
   MYSQL_USER=user
   MYSQL_PASSWORD=pass
   MYSQL_DATABASE=db
   MAIN_SERVER_IP=...
   MAIN_SERVER_USER=...
   SSH_PRIVATE_KEY_PATH=~/.ssh/id_rsa
   HTTP_PROXY_URL=...
   OPENAI_KEY=...
   ASST_ID=...
   EMERGENCY_BOT_TOKEN=...
   BX_WEBHOOK_URL=...
   ```
   Полный список переменных и их назначение можно посмотреть в `config.py`.
4. **Инициализация базы данных**
   ```bash
   python init.py
   ```

## Запуск
1. **Обновление данных**
   ```bash
   python updater.py
   ```
   Скрипт раз в 5 минут загружает данные и обновляет SQLite.
2. **Веб‑приложение**
   ```bash
   python app.py
   ```
   В продакшне используйте Gunicorn:
   ```bash
   gunicorn --workers 3 --bind 127.0.0.1:8000 wsgi:app
   ```
3. **Продакшн**
   Настройте systemd‑юниты для приложения и обновляющего скрипта, проксирование через Nginx и SSL‑сертификат.

## Лицензия
Проект распространяется без явной лицензии.

