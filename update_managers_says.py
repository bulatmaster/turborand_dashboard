from sqlite3 import Row
import os
import time
import re 
from dataclasses import dataclass

import pandas as pd
import mysql.connector
import httpx 
from openai import OpenAI

import config 
import db 


conn = db.get_conn()

mysql_conn   = mysql.connector.connect(**config.MYSQL_CONFIG)

proxy = httpx.Proxy(url=config.HTTP_PROXY_URL)
openai_client = OpenAI(api_key=config.OPENAI_KEY,
                http_client=httpx.Client(transport=httpx.HTTPTransport(proxy=proxy)))



def update_managers_says():
    while True:
        deals = conn.execute(
            """
            SELECT * FROM deals 
            WHERE stage_semantic_id != "F" 
            AND managers_says IS NULL 
            AND date_modify > "2025-07-15"
            ORDER BY id DESC
            """
        ).fetchall()
        for deal in deals:
            try:
                summary = get_summary(deal)
            except Exception as e:
                print(f'{e.__class__.__name__}: {e}')
                summary = 'N/A'
            
            if summary in ('N/A', 'не найдено'):
                summary = ''

            with conn:
                conn.execute(
                    """
                    UPDATE deals SET managers_says = ? WHERE id = ?
                    """, (summary, deal['id'])
                )
        

def get_summary(deal: Row):
    deal_id = deal['id']

    # Get Messages 
    with mysql_conn.cursor(dictionary=True) as cur:
        cur.execute(f"""
            SELECT ID
            FROM b_im_chat
            WHERE ENTITY_TYPE = 'CRM'
                AND (ENTITY_ID = CONCAT('DEAL|', {deal_id}) OR ENTITY_ID = CONCAT('D', {deal_id})
            );
        """)
        chat_id = cur.fetchone()['ID']
        cur.execute(f'SELECT * FROM b_im_message WHERE CHAT_ID = {chat_id}')
        rows = cur.fetchall()

    messages_text = ''
    for row in rows:
        from_id = row['AUTHOR_ID']
        date = row['DATE_CREATE']
        msg_text = row['MESSAGE']
        attachments = row['MESSAGE_OUT']

        msg = (
            f'\n'
            f'От (ID): {from_id}\n'
            f'Дата: {date}\n'
            f'Сообщение: {msg_text}\n'
        )
        if attachments:
            msg += f'Вложения: {attachments}\n'
        
        messages_text += msg 
    
    # AI part 
    user_content = (
        f"""
        Вот история внутреннего чата сотрудников, которые обсуждают сделку в CRM.
        Верни то, что наши сотрудники говорят об этой сделке (1 короткое предложение)
        
        ЕСЛИ НЕ НАШЁЛ, верни "не найдено"

        СООБЩЕНИЯ:
        {messages_text}
        """
    )

    query = [
        {"role": "system", "content": ("Верни то, что сотрудники говорят о сделке (1 предложение), "
                                       "проанализировав внутренний чат сотрудинков ")
        },
        {"role": "user",   "content": user_content},
    ]


    response = openai_client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=query,
        temperature=0.1,
        #max_tokens=300,        
    )
    answer_text = response.choices[0].message.content

    return answer_text


if __name__ == '__main__':
    update_managers_says()