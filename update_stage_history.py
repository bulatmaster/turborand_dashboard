# https://apidocs.bitrix24.ru/api-reference/crm/crm-stage-history-list.html

import requests 

import config 
import db 


conn = db.get_conn()


def update_stage_history():
    method = 'crm.stagehistory.list'

    request_url = f'{config.BX_WEBHOOK_URL}/{method}'

    highest_id_record = conn.execute(
        'SELECT id FROM deals_stage_history ORDER BY id DESC LIMIT 1'
    ).fetchone()
    highest_id = highest_id_record[0] if highest_id_record else 0

    offset = 0

    while True:
        
        r = requests.get(request_url, params={
            "entityTypeId": 2,  # сделка
            "FILTER[>ID]": highest_id,
            "start": offset
        })
        data = r.json()

        to_insert = []
        for rec in data['result']['items']:
            rec_id = rec['ID']
            deal_id = rec['OWNER_ID']
            pipeline_id = rec['CATEGORY_ID']
            stage_id = rec['STAGE_ID']
            stage_semantic_id = rec['STAGE_SEMANTIC_ID']
            record_time = rec['CREATED_TIME']

            to_insert.append((rec_id, deal_id, pipeline_id, stage_id, stage_semantic_id, record_time))
        
        if to_insert:
            with conn:
                conn.executemany(
                    """
                    INSERT INTO deals_stage_history 
                    (id, deal_id, pipeline_id, stage_id, stage_semantic_id, record_time) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, to_insert
                )
        
        if data['total'] - offset <= 50:
            break 

        offset += 50


if __name__ == '__main__':
    update_stage_history()