from datetime import datetime
from typing import Dict, Optional

from app.db.database import get_connection


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class SettingsRepository:
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with get_connection() as conn:
            row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
        if row is None:
            return default
        return str(row["value"])

    def set(self, key: str, value: str) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO app_settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def get_all(self) -> Dict[str, str]:
        with get_connection() as conn:
            rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
        return {str(row["key"]): str(row["value"]) for row in rows}
