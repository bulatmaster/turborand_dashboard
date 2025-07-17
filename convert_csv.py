import re
import csv 
from datetime import datetime, timezone 
from typing import Optional, Dict
import phpserialize                       # pip install phpserialize


def convert_date_format(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        dt = date_str
    
    dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    # Устанавливаем часовой пояс UTC
    dt = dt.replace(tzinfo=timezone.utc)
    # Возвращаем строку в формате ISO 8601
    return dt.isoformat()

# ── вспомогательные ────────────────────────────────────────────────────────
_stage_prefix = re.compile(r"^C(\d+):")

def _category_from_stage(stage: Optional[str]) -> Optional[int]:
    if not stage:
        return None
    m = _stage_prefix.match(stage)
    return int(m.group(1)) if m else None


# ── главный парсер ─────────────────────────────────────────────────────────
def parse_event_line(row: Dict[str, str]) -> Dict[str, Optional[object]]:
    """
    row – словарь одной строки из csv.DictReader.

    Возвращает:
        {
            "deal_id": int,
            "old_category_id": Optional[int],
            "new_category_id": Optional[int],
            "old_stage_id": Optional[str],
            "new_stage_id": Optional[str],
            "record_date": datetime,
        }
    """
    deal_id     = int(row["ASSOCIATED_ENTITY_ID"])
    record_date = convert_date_format(row["CREATED"])
    
        
    settings_raw = row["SETTINGS"]

    result = {
        "deal_id": deal_id,
        "old_category_id": None,
        "new_category_id": None,
        "old_stage_id": None,
        "new_stage_id": None,
        "record_date": record_date,
    }

    # Пустой SETTINGS
    if settings_raw in ("a:0:{}", "a:0:{}"):
        return result

    try:
        settings = phpserialize.loads(settings_raw.encode(), decode_strings=True)
    except Exception:
        # Если десериализация не удалась, возвращаем минимум
        return result

    field_type = settings.get("FIELD")

    # ── смена воронки (CATEGORY_ID) ───────────────────────────────────────
    if field_type == "CATEGORY_ID":
        result["old_category_id"] = settings.get("START_CATEGORY_ID")
        result["new_category_id"] = settings.get("FINISH_CATEGORY_ID")
        result["old_stage_id"]    = settings.get("START_STAGE_ID")
        result["new_stage_id"]    = settings.get("FINISH_STAGE_ID")

    # ── смена стадии (STAGE_ID) ───────────────────────────────────────────
    elif field_type == "STAGE_ID":
        result["old_stage_id"] = settings.get("START")
        result["new_stage_id"] = settings.get("FINISH")
        result["old_category_id"] = _category_from_stage(result["old_stage_id"])
        result["new_category_id"] = _category_from_stage(result["new_stage_id"])

    # остальные FIELD («IS_MANUAL_OPPORTUNITY» и пр.) нам не нужны
    return result


import sqlite3 
conn = sqlite3.connect('database.db')

def main():
    with open('result.csv', mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    # Теперь data — это список словарей:
    with conn:
        for row in rows:
            r = parse_event_line(row)
            conn.execute(
                """
                INSERT INTO deals_stage_history
                (
                deal_id,
                old_pipeline_id,
                old_stage_id,
                new_pipeline_id,
                new_stage_id,
                stage_semantic_id,
                record_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    r['deal_id'],
                    r['old_category_id'],
                    r['old_stage_id'],
                    r['new_category_id'],
                    r['new_stage_id'],
                    None,
                    r['record_date']
                )
            )

    


main()