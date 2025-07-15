import requests 
import json 

from config import BASE_URL



method = 'crm.item.list'
request_url = f'{BASE_URL}/{method}'
r = requests.get(request_url, {
    "entityTypeId": 176,  # Смарт процесс Командировки 
    'start': 50
})

data = r.json()

r = json.dumps(data, indent=2, ensure_ascii=False)

print(r)

with open(f'{method.replace(".", "_")}.json', 'w') as f:
    f.write(r)
    