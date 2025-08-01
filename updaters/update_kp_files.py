from sqlite3 import Row
import os
import time
import re 
from dataclasses import dataclass

import pandas as pd
import mysql.connector
import httpx 
from openai import OpenAI

from utils import emergency_report
import config 
import db 


conn = db.get_conn()

mysql_conn   = mysql.connector.connect(**config.MYSQL_CONFIG)

proxy = httpx.Proxy(url=config.HTTP_PROXY_URL)
openai_client = OpenAI(api_key=config.OPENAI_KEY,
                http_client=httpx.Client(transport=httpx.HTTPTransport(proxy=proxy)))



def update_kps():
    os.makedirs('tmp', exist_ok=True)

    kps_unprocessed = conn.execute(
        'SELECT * FROM kp_files WHERE summary IS NULL ORDER BY file_id DESC'
    ).fetchall()

    for kp in kps_unprocessed:
        try:
            update_kp(kp)
        except Exception as e:
            emergency_report(f'update_kps: {e.__class__.__name__}: {e}')
            print(f'{e.__class__.__name__}: {e}')


def update_kp(kp: Row):
    file_id = kp["file_id"]

    data = get_file_data(file_id)

    summary = None

    try:

        if str(data.kp_date) > '2025-05':
            file_path = copy_file(data.remote_file_path, data.original_file_name)

            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                file_path = excel_to_json(file_path)

            summary = summarize(file_path)
            
            summary = clear_model_response(summary)

            os.remove(file_path)

    except Exception as e:
        print(f'{e.__class__.__name__}: {e}')
        
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
    

def copy_file(remote_path, original_name) -> str:
    os.makedirs('tmp', exist_ok=True)
    local_path = f'tmp/{original_name}'
    cmd = f'scp turborand:"{remote_path}" "{local_path}"'
    os.system(cmd)
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
    

    # 1. Upload Files 
    file = openai_client.files.create(file=open(file_path, "rb"), purpose="assistants")
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

    return result
    


def clear_model_response(text):
    return re.sub(r'【[^【】]+?】', '', text)


if __name__ == '__main__':
    update_kps()