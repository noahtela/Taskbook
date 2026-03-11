from datetime import datetime
from typing import Any, Dict, List, Optional

from app.db.database import get_connection


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class PromptTemplateRepository:
    def list_templates(self, scene: str = "daily_report") -> List[Dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, scene, name, template_text, is_active, created_at, updated_at
                FROM prompt_templates
                WHERE scene = ?
                ORDER BY is_active DESC, id DESC
                """,
                (scene,),
            ).fetchall()

        return [dict(row) for row in rows]

    def get_active_template(self, scene: str = "daily_report") -> Optional[Dict[str, Any]]:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT id, scene, name, template_text, is_active, created_at, updated_at
                FROM prompt_templates
                WHERE scene = ? AND is_active = 1
                ORDER BY id DESC
                LIMIT 1
                """,
                (scene,),
            ).fetchone()

        return dict(row) if row else None

    def save_template(
        self,
        scene: str,
        name: str,
        template_text: str,
        is_active: bool,
        template_id: Optional[int] = None,
    ) -> int:
        ts = now_iso()
        with get_connection() as conn:
            if is_active:
                conn.execute("UPDATE prompt_templates SET is_active = 0 WHERE scene = ?", (scene,))

            if template_id is None:
                cur = conn.execute(
                    """
                    INSERT INTO prompt_templates (scene, name, template_text, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (scene, name, template_text, 1 if is_active else 0, ts, ts),
                )
                return int(cur.lastrowid)

            conn.execute(
                """
                UPDATE prompt_templates
                SET name = ?, template_text = ?, is_active = ?, updated_at = ?
                WHERE id = ?
                """,
                (name, template_text, 1 if is_active else 0, ts, template_id),
            )
            return template_id

    def set_active(self, template_id: int) -> None:
        with get_connection() as conn:
            row = conn.execute("SELECT scene FROM prompt_templates WHERE id = ?", (template_id,)).fetchone()
            if row is None:
                return
            scene = row["scene"]
            conn.execute("UPDATE prompt_templates SET is_active = 0 WHERE scene = ?", (scene,))
            conn.execute(
                "UPDATE prompt_templates SET is_active = 1, updated_at = ? WHERE id = ?",
                (now_iso(), template_id),
            )

    def get_template_by_id(self, template_id: int) -> Optional[Dict[str, Any]]:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT id, scene, name, template_text, is_active, created_at, updated_at
                FROM prompt_templates
                WHERE id = ?
                """,
                (template_id,),
            ).fetchone()
        return dict(row) if row else None
