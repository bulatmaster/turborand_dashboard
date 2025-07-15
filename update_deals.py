import requests 

import config 
import db 


conn = db.get_conn()


def parse_to_int(value: str) -> int:
    if not value:
        return None
    # Отделим число от возможных суффиксов (например, |RUB)
    number_part = value.split('|')[0]
    # Преобразуем к float и затем к int (отбрасывается дробная часть)
    return int(float(number_part))


def update_deals():
    method = 'crm.deal.list'

    request_url = f'{config.BX_WEBHOOK_URL}/{method}'

    highest_id_deal = conn.execute('SELECT id FROM deals ORDER BY id DESC LIMIT 1').fetchone()
    highest_id = highest_id_deal[0] if highest_id_deal else 0

    offset = 0

    while True:
        
        r = requests.get(request_url, params={
            'select[]': ['*', 'UF_*'],
            "FILTER[>ID]": highest_id,
            "start": offset
        })
        data = r.json()

        to_insert = []
        for deal in data['result']:
            deal_id = deal['ID']
            sales_user_id = deal['ASSIGNED_BY_ID']
            supply_user_id = deal['UF_CRM_1719307895']
            pipeline_id = deal['CATEGORY_ID']
            stage_id = deal['STAGE_ID']
            stage_semantic_id = deal['STAGE_SEMANTIC_ID']
            opportunity = parse_to_int(deal['OPPORTUNITY'])
            profit = parse_to_int(deal['UF_CRM_1745583203057'])

            to_insert.append((deal_id, 
                              sales_user_id, 
                              supply_user_id, 
                              pipeline_id, 
                              stage_id, 
                              stage_semantic_id, 
                              opportunity, 
                              profit))
        
        if to_insert:
            with conn:
                conn.executemany(
                    """
                    INSERT INTO deals (  
                        id, 
                        sales_user_id, 
                        supply_user_id, 
                        pipeline_id, 
                        stage_id, 
                        stage_semantic_id, 
                        opportunity, 
                        profit
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, to_insert
                )
        
        if data['total'] - offset <= 50:
            break 

        offset += 50


if __name__ == '__main__':
    update_deals()