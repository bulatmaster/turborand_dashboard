import sqlite3 

conn = sqlite3.connect('database.db')

deals = [str(deal_id) for (deal_id,) in conn.execute(
    'SELECT id FROM deals WHERE date_modify > "2025-07-01"'
).fetchall()]

with open('deal_ids.txt', 'w') as f:
    f.write(",".join(deals))
