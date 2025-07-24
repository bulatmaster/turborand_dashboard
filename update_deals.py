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
            sales_user_id = deal['ASSIGNED_BY_ID']
            supply_user_id = deal['UF_CRM_1719307895']
            pipeline_id = deal['CATEGORY_ID']
            stage_id = deal['STAGE_ID']
            stage_semantic_id = deal['STAGE_SEMANTIC_ID']
            opportunity = money_to_int(deal['OPPORTUNITY'])
            profit = money_to_int(deal['UF_CRM_1745583203057'])
            date_modify = deal['DATE_MODIFY']

            if deal_id in deals_db:
                with conn:
                    conn.execute(
                        """
                        UPDATE deals SET 
                            sales_user_id = ?,
                            supply_user_id = ?,
                            pipeline_id = ?,
                            stage_id = ?,
                            stage_semantic_id = ?,
                            opportunity = ?,
                            profit = ?,
                            date_modify = ?
                        WHERE id = ?
                        """, (
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
                with conn:
                    conn.execute(
                        """
                        INSERT INTO deals (  
                            id, 
                            sales_user_id, 
                            supply_user_id, 
                            pipeline_id, 
                            stage_id, 
                            stage_semantic_id, 
                            opportunity, 
                            profit,
                            date_modify
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (deal_id, 
                              sales_user_id, 
                              supply_user_id, 
                              pipeline_id, 
                              stage_id, 
                              stage_semantic_id, 
                              opportunity, 
                              profit, 
                              date_modify)
                    )
            
        
        if data['total'] - offset <= 50:
            break 

        offset += 50


if __name__ == '__main__':
    update_deals()