from datetime import datetime
from typing import Any, Dict, List, Optional

from app.db.database import get_connection


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class AIModelConfigRepository:
    def list_configs(self) -> List[Dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, name, base_url, model_name, temperature, max_tokens, is_active, created_at, updated_at
                FROM ai_model_configs
                ORDER BY is_active DESC, id DESC
                """
            ).fetchall()

        return [dict(row) for row in rows]

    def get_active_config(self) -> Optional[Dict[str, Any]]:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT id, name, base_url, model_name, api_key, temperature, max_tokens, is_active, created_at, updated_at
                FROM ai_model_configs
                WHERE is_active = 1
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()

        return dict(row) if row else None

    def save_config(
        self,
        name: str,
        base_url: str,
        model_name: str,
        api_key: str,
        temperature: float,
        max_tokens: Optional[int],
        is_active: bool,
        config_id: Optional[int] = None,
    ) -> int:
        ts = now_iso()
        with get_connection() as conn:
            if is_active:
                conn.execute("UPDATE ai_model_configs SET is_active = 0")

            if config_id is None:
                cur = conn.execute(
                    """
                    INSERT INTO ai_model_configs
                    (name, base_url, model_name, api_key, temperature, max_tokens, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (name, base_url, model_name, api_key, temperature, max_tokens, 1 if is_active else 0, ts, ts),
                )
                return int(cur.lastrowid)

            conn.execute(
                """
                UPDATE ai_model_configs
                SET name = ?, base_url = ?, model_name = ?, api_key = ?, temperature = ?, max_tokens = ?, is_active = ?, updated_at = ?
                WHERE id = ?
                """,
                (name, base_url, model_name, api_key, temperature, max_tokens, 1 if is_active else 0, ts, config_id),
            )
            return config_id

    def set_active(self, config_id: int) -> None:
        with get_connection() as conn:
            conn.execute("UPDATE ai_model_configs SET is_active = 0")
            conn.execute("UPDATE ai_model_configs SET is_active = 1, updated_at = ? WHERE id = ?", (now_iso(), config_id))

    def get_config_by_id(self, config_id: int) -> Optional[Dict[str, Any]]:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT id, name, base_url, model_name, api_key, temperature, max_tokens, is_active, created_at, updated_at
                FROM ai_model_configs
                WHERE id = ?
                """,
                (config_id,),
            ).fetchone()
        return dict(row) if row else None
