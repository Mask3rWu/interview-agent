import json
import uuid
from pathlib import Path
from app.core.config import DB_PATH


def _load_db() -> dict:
    if not DB_PATH.exists():
        return {}
    with open(DB_PATH, "r") as f:
        return json.load(f)


def _save_db(data: dict) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DB_PATH, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def _ensure_table(table: str) -> dict:
    db = _load_db()
    if table not in db:
        db[table] = {}
    return db


def insert(table: str, record: dict) -> dict:
    db = _ensure_table(table)
    rid = str(uuid.uuid4())
    record["id"] = rid
    db[table][rid] = record
    _save_db(db)
    return record


def get(table: str, rid: str) -> dict | None:
    db = _load_db()
    return db.get(table, {}).get(rid)


def list_all(table: str) -> list[dict]:
    db = _load_db()
    return list(db.get(table, {}).values())


def update(table: str, rid: str, record: dict) -> dict | None:
    db = _load_db()
    if table not in db or rid not in db[table]:
        return None
    db[table][rid].update(record)
    _save_db(db)
    return db[table][rid]


def replace_table(table: str, records: dict) -> None:
    db = _load_db()
    db[table] = records
    _save_db(db)


def delete(table: str, rid: str) -> bool:
    db = _load_db()
    if table not in db or rid not in db[table]:
        return False
    del db[table][rid]
    _save_db(db)
    return True
