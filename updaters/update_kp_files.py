from sqlite3 import Row
import os
import time
import re 
from dataclasses import dataclass

import pandas as pd
import mysql.connector
import httpx 
from openai import OpenAI
import openai 
import paramiko

from utils import emergency_report
import config 
import db 


conn = db.get_conn()

mysql_conn   = mysql.connector.connect(**config.MYSQL_CONFIG)

proxy = httpx.Proxy(url=config.HTTP_PROXY_URL)
openai_client = OpenAI(api_key=config.OPENAI_KEY,
                http_client=httpx.Client(transport=httpx.HTTPTransport(proxy=proxy)))


openai_allowed_extensions = [
    ".c", ".cpp", ".cs", ".css", ".doc", ".docx", ".go", ".html", ".java",
    ".js", ".json", ".md", ".pdf", ".php", ".pptx", ".py", ".rb", ".sh",
    ".tex", ".ts", ".txt"
]

OFFSET_DATE = '2025-05'  # Дата, документы раньше которой ничего не делаем 


def update_kps():
    kps_unprocessed = conn.execute(
        'SELECT * FROM kp_files WHERE summary IS NULL ORDER BY file_id DESC'
    ).fetchall()

    for kp in kps_unprocessed:
        try:
            update_kp_summary(kp)
        except mysql.connector.errors.OperationalError as e: 
            emergency_report(f'update_kps: произошла ошибка {e.__class__.__name__}: {e}, пропускаю обновление КП')
            return 

def update_kp_summary(kp: Row):
    file_id = kp["file_id"]

    data: FileData = get_file_data(file_id)
    remote_file_path = data.remote_file_path
    original_file_name = data.original_file_name
    file_modified_date = data.kp_date

    summary = None
    if str(data.kp_date) > OFFSET_DATE:

        local_file_path = copy_file(data.remote_file_path, data.original_file_name)

        if local_file_path.lower().endswith(('.xlsx', '.xls', '.xlsm')):
            local_file_path = excel_to_json(local_file_path)

        summary = summarize(local_file_path)
        
        os.remove(local_file_path)

        
    with conn:
        conn.execute(
            """
            UPDATE kp_files SET
                kp_date = ?,
                original_file_name = ?,
                remote_file_path = ?,
                summary = ?
            WHERE file_id = ?
            """, 
            (data.kp_date, data.original_file_name, data.remote_file_path, summary, file_id)
        )


@dataclass 
class FileData:
    kp_date: str
    original_file_name: str
    remote_file_path: str
    

def get_file_data(file_id):
    """
    Получает данные о файле с MySQL
    """
    with mysql_conn.cursor(dictionary=True) as cur:
        cur.execute(f'SELECT * FROM b_file WHERE ID = {file_id}')
        row = cur.fetchone()

    if not row:
        return None 

    subdir = row['SUBDIR']
    file_name = row['FILE_NAME']
    original_name = row['ORIGINAL_NAME']
    kp_date = row['TIMESTAMP_X']
    remote_path = f'/home/bitrix/www/upload/{subdir}/{file_name}'
    
    return FileData(
        kp_date=kp_date,
        original_file_name=original_name,
        remote_file_path=remote_path
    )
    

def copy_file(remote_path: str, original_name: str) -> str:
    # Настройки подключения вручную, т.к. .ssh/config не поддерживается
    ssh_host = config.MAIN_SERVER_IP                # IP-адрес turborand
    ssh_user = config.MAIN_SERVER_USER              # Пользователь
    ssh_key_path = config.SSH_PRIVATE_KEY_PATH   # Приватный ключ

    # Создание локальной папки
    os.makedirs("tmp", exist_ok=True)
    local_path = f"tmp/{original_name}"

    # Загрузка файла через SFTP
    key = paramiko.Ed25519Key.from_private_key_file(ssh_key_path)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=ssh_host, username=ssh_user, pkey=key)

    sftp = ssh.open_sftp()
    sftp.get(remote_path, local_path)
    sftp.close()
    ssh.close()

    return local_path


def excel_to_json(excel_path):
    # Проверка существования файла
    if not os.path.isfile(excel_path):
        raise FileNotFoundError(f"Файл не найден: {excel_path}")
    
    # Чтение Excel файла
    df = pd.read_excel(excel_path)

    # Получение имени и директории
    base_dir = os.path.dirname(excel_path)
    base_name = os.path.splitext(os.path.basename(excel_path))[0]
    json_path = os.path.join(base_dir, f"{base_name}.json")

    # Сохранение в JSON
    df.to_json(json_path, orient='records', force_ascii=False, indent=4)

    os.remove(excel_path)

    return json_path


def summarize(file_path: str) -> str:
    PROMPT = """
        Напиши в одном предложении 
        ОБЪЕКТ прикрепленного коммерческого предложения 
        (что именно продаём) + ИТОГОВАЯ сумма сделки.

        ПРИМЕРЫ ОТВЕТОВ (возвращай без кавычек):
        "ТО компрессора <модель оборудования> за 1 000 000 ₽"
        "Продажа компрессора <модель оборудования> за 15 000 000 ₽"
        "Продажа и пусконаладочные работы оборудования <модель оборудования> за 25 500 125₽"

        НЕ добавляй вводные конструкции вроде "Объект предложения: ...",  
        "Объектом предложения является ..."
        НЕ включая излишние подробности, например точные длинные серийные номера оборудования 
        (достаточно марки / основного названия модели)
        Если не нашел, верни "" (пустую строку)
    """

    # 0. Validate Files 
    if not file_path.lower().endswith(tuple(openai_allowed_extensions)):
        return ''

    # 1. Upload Files 
    try:
        file = openai_client.files.create(file=open(file_path, "rb"), purpose="assistants")
    except openai.BadRequestError as e:
        error_data = e.response.json() if e.response else {}
        error_message = error_data.get("error", {}).get("message", "")
        if "File is empty" in error_message:
            return ''
        else:
            raise 


    attachments = [{"file_id": file.id, "tools": [{"type": "file_search"}]}]
        
    # 2. создаём thread с сообщением‑вложением ------------------------------------

    thread = openai_client.beta.threads.create(messages=[{
        "role": "user",
        "content": PROMPT,
        "attachments": attachments
    }])

    # 3. запускаем ассистента ------------------------------------------------------
    run = openai_client.beta.threads.runs.create(thread_id=thread.id, assistant_id=config.ASST_ID)

    while True:                                    # ждём окончания run
        run = openai_client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run.status in ("completed", "failed"):
            break
        time.sleep(1)

    # 4. получаем последнее сообщение ассистента -----------------------------------
    reply = openai_client.beta.threads.messages.list(thread_id=thread.id, order="desc").data[0]
    result = reply.content[0].text.value

    # 5. Очистка от вставленных цитат 
    result = re.sub(r'【[^【】]+?】', '', result)

    return result
    

if __name__ == '__main__':
    update_kps()