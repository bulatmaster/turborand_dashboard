import requests 

import config 
import db 
from utils import money_to_int


conn = db.get_conn()



def update_deals():
    METHOD = 'crm.deal.list'
    REQUEST_URL = f'{config.BX_WEBHOOK_URL}/{METHOD}'

    last_modify_deal = conn.execute(
        'SELECT date_modify FROM deals ORDER BY date_modify DESC LIMIT 1'
    ).fetchone()

    deals_db = {row[0] for row in conn.execute('SELECT id FROM deals').fetchall()}

    offset = 0
    while True:
        params = {
            'select[]': ['*', 'UF_*'],
            "ORDER[DATE_MODIFY]": "ASC",
            "start": offset
        }
        if last_modify_deal:
            params["FILTER[>DATE_MODIFY]"] = last_modify_deal[0],

        r = requests.get(REQUEST_URL, params=params)
        data = r.json()

        for deal in data['result']:
            deal_id = int(deal['ID'])
            title = deal['TITLE']
            type_id = deal['TYPE_ID']
            sales_user_id = deal['ASSIGNED_BY_ID']
            supply_user_id = deal['UF_CRM_1719307895']
            pipeline_id = deal['CATEGORY_ID']
            stage_id = deal['STAGE_ID']
            stage_semantic_id = deal['STAGE_SEMANTIC_ID']
            opportunity = money_to_int(deal['OPPORTUNITY'])
            profit = money_to_int(deal['UF_CRM_1745583203057'])
            date_modify = deal['DATE_MODIFY']
            kp_files = deal['UF_CRM_1681378238969']

            if deal_id in deals_db:
                conn.execute(
                    """
                    UPDATE deals SET 
                        title = ?,
                        type_id = ?,
                        sales_user_id = ?,
                        supply_user_id = ?,
                        pipeline_id = ?,
                        stage_id = ?,
                        stage_semantic_id = ?,
                        opportunity = ?,
                        profit = ?,
                        date_modify = ?,
                        managers_says = NULL
                    WHERE id = ?
                    """, (
                        title,
                        type_id,
                        sales_user_id, 
                        supply_user_id, 
                        pipeline_id, 
                        stage_id, 
                        stage_semantic_id, 
                        opportunity, 
                        profit,
                        date_modify,
                        deal_id
                    )
                )
            else:
                conn.execute(
                    """
                    INSERT INTO deals (  
                        id, 
                        title,
                        type_id,
                        sales_user_id, 
                        supply_user_id, 
                        pipeline_id, 
                        stage_id, 
                        stage_semantic_id, 
                        opportunity, 
                        profit,
                        date_modify
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        deal_id, 
                        title,
                        type_id,
                        sales_user_id, 
                        supply_user_id, 
                        pipeline_id, 
                        stage_id, 
                        stage_semantic_id, 
                        opportunity, 
                        profit, 
                        date_modify,
                    )
                )

            for kp in kp_files:
                file_id = int(kp['id'])
                show_url = kp['showUrl']
                download_url = kp['downloadUrl']
    
                conn.execute(
                    """
                    INSERT OR IGNORE INTO kp_files
                    (file_id, deal_id, show_url, download_url) 
                    VALUES (?, ?, ?, ?)
                    """, (file_id, deal_id, show_url, download_url)
                )        
        
        conn.commit()
        
        if data['total'] - offset <= 50:
            break 

        offset += 50


if __name__ == '__main__':
    update_deals()