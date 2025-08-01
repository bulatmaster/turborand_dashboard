ДАШБОРД TURBODESK

--- СУТЬ ---
2 процесса 
1) app.py - flask-приложение (сам дашборд)
2) updater.py  (обновление данных)


updater.py представляет собой скрипт, который периодически запускает 
отдельные скрипты: update_users.py , update_deals.py и т.д. 

Эти отдельные скрипты получают данные по API 
(или иногда напрямую из ДБ),
как-то их обрабатывают (например прогоняют через API OpenAI)
и складывают во внутреннюю sqlite базу данных.


app.py представляет собой flask-приложение, которое забирает актуальные данные
из внутренней ДБ и отдаёт на html шаблон.



--- ТРЕБОВАНИЯ ---
VPS сервер с Ubuntu 24.04.
Конфигурация подойдёт самая простая, типа 1 ГБ RAM, 1 ядро, 10-20 ГБ диск 

--- ПОДГОТОВКА К ЗАПУСКУ ---
1. Клонировать репозиторий на сервер

2. установить зависимости  (лучше внутри виртуального окружения (venv))
pip install -r requirements.txt 

3. создать .env файл в корне проекта, прописать туда данные согласно config.py
(то что запрашивается через getenv('SOME_PARAMETER'))

4. Инициировать sqlite базу данных 
python init.py 

--- ТЕСТОВЫЙ ЗАПУСК ---

1. запустить updater.py 

2. запустить app.py  - дашборд будет открываться 

--- ПРОДАКШН ЗАПУСК --- 

1. Создать и запустить systemd-юнит, который будет отвечать за сам дашборд 
(запускать app.py через Gunicorn)

Пример юнита:

[Unit]
Description=TURBORAND DASHBOARD
After=network.target

[Service]
User=turborand
Group=turborand
WorkingDirectory=/home/turborand/turborand_dashboard
ExecStart=/home/turborand/turborand_dashboard/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 wsgi:app
Environment="PATH=/home/turborand/turborand/venv/bin"

[Install]
WantedBy=multi-user.target


2. Создать и запустить systemd-юнит, который будет отвечать за updater.py 

Пример юнита:

[Unit]
Description=TURBORAND DASHBOARD
After=network.target

[Service]
User=turborand
Group=turborand
WorkingDirectory=/home/turborand/turborand_dashboard
ExecStart=/home/turborand/turborand_dashboard/venv/bin/python3 updater.py
Environment="PATH=/home/turborand/turborand/venv/bin"
StandardOutput=append:/home/turborand/turborand_dashboard/logs/updater.log
StandardError=inherit

[Install]
WantedBy=multi-user.target


3. Настроить nginx, чтобы пересылал запросы к Gunicorn 

4. Получить SSL-сертификат через certbot 

