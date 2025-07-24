import requests 

import config 
import db 


conn = db.get_conn()


def update_trips():
    method = 'crm.item.list'

    request_url = f'{config.BX_WEBHOOK_URL}/{method}'

    last_modify_trip = conn.execute(
        'SELECT date_modify FROM trips ORDER BY date_modify DESC LIMIT 1'
    ).fetchone()


    offset = 0

    while True:
        params = {
            "entityTypeId": 176,  # Смарт процесс Командировки 
            "start": offset
        }
        if last_modify_trip:
            params["FILTER[>updatedTime]"] = last_modify_trip[0],
        
        r = requests.get(request_url, params=params)
        data = r.json()

        trips_db = {row[0] for row in conn.execute(
            'SELECT id FROM trips'
        ).fetchall()}

        for trip in data['result']['items']:
            trip_id = int(trip['id'])
            user_id = trip['assignedById']
            stage_id = trip['stageId']
            start_time = trip['begindate']
            end_time = trip['closedate']
            date_modify = trip['updatedTime']

            if trip_id in trips_db:
                conn.execute(
                    """
                    UPDATE trips SET
                        user_id = ?, 
                        stage_id = ?, 
                        begin_time = ?, 
                        end_time = ?, 
                        date_modify = ?
                    WHERE id = ?
                    """, 
                    (user_id, stage_id, start_time, end_time, date_modify, trip_id)
                )
            else:
                conn.execute(
                    """
                    INSERT INTO trips 
                    (id, user_id, stage_id, begin_time, end_time, date_modify) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, 
                    (trip_id, user_id, stage_id, start_time, end_time, date_modify)
                )

        
        if data['total'] - offset <= 50:
            break 

        offset += 50

    conn.commit()

if __name__ == '__main__':
    update_trips()