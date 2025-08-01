import os
import re
import mysql.connector
import sqlite3
import phpserialize
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Iterable, List
from zoneinfo import ZoneInfo          

from config import MYSQL_CONFIG
import db 




################################################################################
# Конфигурация
################################################################################


SQLITE_PATH = os.getenv("SQLITE_PATH", "database.db")
BATCH_SIZE  = int(os.getenv("BATCH_SIZE", 10_000))



################################################################################
# Утилиты преобразования дат и стадий
################################################################################


def convert_date_format(value) -> str:
    """
    Принимает datetime | str | None и возвращает ISO‐8601 в UTC
    (YYYY‑MM‑DDTHH:MM:SS+00:00).

    Поддерживаемые строковые форматы:
      • 'dd.mm.YYYY HH:MM:SS'
      • 'YYYY-mm-dd HH:MM:SS'
    """
    # 1) уже datetime
    if isinstance(value, datetime):
        dt = value

    # 2) строка → пробуем два формата
    elif isinstance(value, str):
        for fmt in ("%d.%m.%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(value, fmt)
                break
            except ValueError:
                dt = None
        if dt is None:
            raise ValueError(f"Unrecognised date format: {value!r}")

    else:
        raise TypeError(f"CREATED value must be str or datetime, got {type(value)}")

    # 3) делаем aware‑datetime в UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    else:
        dt = dt.astimezone(ZoneInfo("UTC"))

    return dt.isoformat(timespec="seconds")


def _category_from_stage(stage: Optional[str]) -> Optional[int]:
    _stage_prefix = re.compile(r"^C(\d+):")

    if not stage:
        return None
    m = _stage_prefix.match(stage)
    return int(m.group(1)) if m else None

################################################################################
# Парсер строки из b_crm_timeline
################################################################################
def parse_event_line(row: Dict[str, str]) -> Dict[str, Optional[object]]:
    """
    Принимает строку‑словарь из MySQL (keys: ID, ASSOCIATED_ENTITY_ID,
    CREATED, SETTINGS) и возвращает dict для вставки в SQLite.
    """
    record_id   = int(row["ID"])                         # новое поле
    deal_id     = int(row["ASSOCIATED_ENTITY_ID"])
    record_date = convert_date_format(row["CREATED"])

    settings_raw = row["SETTINGS"]

    result = {
        "id": record_id,             # <-- сохранится в колонку 'id'
        "deal_id": deal_id,
        "old_category_id": None,
        "new_category_id": None,
        "old_stage_id": None,
        "new_stage_id": None,
        "stage_semantic_id": None,   # зарезервировано, сейчас None
        "record_date": record_date,
    }

    # пустой SETTINGS
    if settings_raw in ("a:0:{}", "a:0:{}"):
        return result

    try:
        settings = phpserialize.loads(settings_raw.encode(), decode_strings=True)
    except Exception:
        return result

    field_type = settings.get("FIELD")

    # смена воронки
    if field_type == "CATEGORY_ID":
        result["old_category_id"] = settings.get("START_CATEGORY_ID")
        result["new_category_id"] = settings.get("FINISH_CATEGORY_ID")
        result["old_stage_id"]    = settings.get("START_STAGE_ID")
        result["new_stage_id"]    = settings.get("FINISH_STAGE_ID")

    # смена стадии
    elif field_type == "STAGE_ID":
        result["old_stage_id"]    = settings.get("START")
        result["new_stage_id"]    = settings.get("FINISH")
        result["old_category_id"] = _category_from_stage(result["old_stage_id"])
        result["new_category_id"] = _category_from_stage(result["new_stage_id"])

    return result

################################################################################
# Чтение батчей из MySQL
################################################################################
def fetch_batches(
    conn: mysql.connector.MySQLConnection,
    start_id: int,
    batch_size: int = BATCH_SIZE
) -> Iterable[List[Dict[str, str]]]:
    """Генератор батчей словарей (строки MySQL)."""
    sql = (
        "SELECT ID, ASSOCIATED_ENTITY_ID, CREATED, SETTINGS "
        "FROM b_crm_timeline "
        "WHERE ID > %s "
        "ORDER BY ID "
        "LIMIT %s"
    )
    while True:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(sql, (start_id, batch_size))
            rows = cur.fetchall()
        if not rows:
            break
        yield rows
        start_id = rows[-1]["ID"]     # следующий батч начинается после последнего

################################################################################
# SQLite helpers
################################################################################
def get_last_saved_id(sqlite_conn: sqlite3.Connection) -> int:
    cur = sqlite_conn.execute("SELECT COALESCE(MAX(id), 0) FROM deals_stage_history")
    return cur.fetchone()[0] or 0

def insert_batch(sqlite_conn: sqlite3.Connection, parsed_rows: List[Dict[str, object]]):
    sql = """
        INSERT INTO deals_stage_history (
            id,
            deal_id,
            old_pipeline_id,
            old_stage_id,
            new_pipeline_id,
            new_stage_id,
            stage_semantic_id,
            record_time
        )
        VALUES (:id, :deal_id, :old_category_id, :old_stage_id,
                :new_category_id, :new_stage_id,
                :stage_semantic_id, :record_date)
    """
    sqlite_conn.executemany(sql, parsed_rows)

################################################################################
# Главная функция
################################################################################
def update_stage_history():
    # --- connect ---
    mysql_conn   = mysql.connector.connect(**MYSQL_CONFIG)
    sqlite_conn  = db.get_conn()
    

    try:
        last_id = get_last_saved_id(sqlite_conn)
        logging.debug("Last imported id = %s", last_id)

        total_imported = 0
        for batch in fetch_batches(mysql_conn, start_id=last_id, batch_size=BATCH_SIZE):
            parsed = [parse_event_line(row) for row in batch]

            # ── парсим и сразу отбрасываем «пустые» переходы ────────────────────────
            parsed: List[Dict[str, object]] = []
            for row in batch:
                r = parse_event_line(row)
                if r["new_stage_id"] is None and r["new_category_id"] is None:
                    # ни стадия, ни воронка не изменились – пропускаем
                    continue
                parsed.append(r)

            if not parsed:            # весь батч оказался «пустым»
                continue

            with sqlite_conn:
                insert_batch(sqlite_conn, parsed)
            total_imported += len(parsed)
            logging.debug("Imported %d rows (up to ID %d)", total_imported, parsed[-1]["id"])

        logging.debug("Done. Total new rows: %d", total_imported)

    finally:
        mysql_conn.close()
        sqlite_conn.close()

################################################################################
if __name__ == "__main__":
    update_stage_history()
