from sqlite3 import Row

import mysql.connector
import httpx 
from openai import OpenAI

import config 
import db 


conn = db.get_conn()

proxy = httpx.Proxy(url=config.HTTP_PROXY_URL)
openai_client = OpenAI(api_key=config.OPENAI_KEY,
                http_client=httpx.Client(transport=httpx.HTTPTransport(proxy=proxy)))


class ChatNotFoundError(Exception):
    pass 


def update_fail_reasons():
    deals = conn.execute(
        """
        SELECT * FROM deals 
        WHERE stage_semantic_id = "F" 
        AND fail_reason IS NULL 
        AND date_modify > "2025-05"
        ORDER BY id DESC
        """
    ).fetchall()
    for deal in deals:
        try:
            reason = calculate_reason(deal)
        except ChatNotFoundError:  # не найден чат сотрудников  
            reason = 'N/A' 
        
        if reason in ('N/A', 'не найдено'):
            reason = 'N/A'

        with conn:
            conn.execute(
                """
                UPDATE deals SET fail_reason = ? WHERE id = ?
                """, (reason, deal['id'])
            )
        

def calculate_reason(deal: Row):
    deal_id = deal['id']

    # Get Messages 
    with mysql.connector.connect(**config.MYSQL_CONFIG) as mysql_conn:
        with mysql_conn.cursor(dictionary=True) as cur:
            cur.execute(f"""
                SELECT ID
                FROM b_im_chat
                WHERE ENTITY_TYPE = 'CRM'
                    AND (ENTITY_ID = CONCAT('DEAL|', {deal_id}) OR ENTITY_ID = CONCAT('D', {deal_id})
                );
            """)
            row = cur.fetchone()
            if not row:
                raise ChatNotFoundError
            chat_id = row['ID']
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
        Сделка провалена. 
        Проанализируй общение сотрудников и попробуй найти причину провала сделки или отказа клиента.
        Верни ТОЛЬКО причину провала сделки (1 короткое предложение)
        
        ЕСЛИ НЕ НАШЁЛ, верни "не найдено"

        СООБЩЕНИЯ:
        {messages_text}
        """
    )

    query = [
        {"role": "system", "content": ("Верни причину провала сделки в 1 предложение, "
                                       "проанализировав внутренний чат сотрудинков, "
                                       "обсуждающих эту сделку.")
        },
        {"role": "user",   "content": user_content},
    ]


    response = openai_client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=query,
        temperature=0.1,
    )
    answer_text = response.choices[0].message.content

    return answer_text


if __name__ == '__main__':
    update_fail_reasons()