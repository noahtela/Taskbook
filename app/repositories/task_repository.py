from datetime import datetime, timedelta
from typing import List, Optional

from app.db.database import get_connection
from app.models.task import Task


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _build_in_clause_params(ids: List[int]) -> str:
    return ",".join(["?"] * len(ids))


class TaskRepository:
    def create_task(
        self,
        title: str,
        description: str = "",
        status: str = "todo",
        priority: int = 2,
        due_date: Optional[str] = None,
    ) -> int:
        ts = now_iso()
        completed_at = ts if status == "done" else None
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO tasks (title, description, status, priority, due_date, created_at, updated_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (title, description, status, priority, due_date, ts, ts, completed_at),
            )
            return cur.lastrowid

    def list_tasks(self, keyword: str = "", status: Optional[str] = None, due_filter: str = "all") -> List[Task]:
        where_clauses = []
        params: List[str] = []

        if keyword:
            where_clauses.append("(title LIKE ? OR description LIKE ?)")
            kw = f"%{keyword}%"
            params.extend([kw, kw])

        if status:
            where_clauses.append("status = ?")
            params.append(status)

        if due_filter and due_filter != "all":
            now = datetime.now()
            if due_filter == "today":
                start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            elif due_filter == "week":
                start = now - timedelta(days=now.weekday())
                start = start.replace(hour=0, minute=0, second=0, microsecond=0)
                end = start + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
            elif due_filter == "month":
                start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if start.month == 12:
                    next_month = start.replace(year=start.year + 1, month=1)
                else:
                    next_month = start.replace(month=start.month + 1)
                end = next_month - timedelta(microseconds=1)
            else:
                start = None
                end = None

            if start is not None and end is not None:
                where_clauses.append("due_date IS NOT NULL AND due_date BETWEEN ? AND ?")
                params.append(start.strftime("%Y-%m-%d %H:%M:%S"))
                params.append(end.strftime("%Y-%m-%d %H:%M:%S"))

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        sql = f"""
            SELECT * FROM tasks
            {where_sql}
            ORDER BY
                CASE status WHEN 'todo' THEN 1 WHEN 'doing' THEN 2 WHEN 'done' THEN 3 ELSE 4 END,
                priority ASC,
                id DESC
        """

        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()

        return [self._row_to_task(row) for row in rows]

    def list_tasks_by_ids(self, task_ids: List[int]) -> List[Task]:
        if not task_ids:
            return []

        placeholders = _build_in_clause_params(task_ids)
        sql = f"SELECT * FROM tasks WHERE id IN ({placeholders})"

        with get_connection() as conn:
            rows = conn.execute(sql, task_ids).fetchall()

        task_map = {int(row["id"]): self._row_to_task(row) for row in rows}
        return [task_map[task_id] for task_id in task_ids if task_id in task_map]

    def get_task(self, task_id: int) -> Optional[Task]:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

        if row is None:
            return None

        return self._row_to_task(row)

    def update_task(
        self,
        task_id: int,
        title: str,
        description: str,
        status: str,
        priority: int,
        due_date: Optional[str],
    ) -> None:
        task = self.get_task(task_id)
        if task is None:
            return

        ts = now_iso()
        if status == "done":
            completed_at = task.completed_at or ts
        else:
            completed_at = None

        with get_connection() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET title = ?, description = ?, status = ?, priority = ?, due_date = ?, updated_at = ?, completed_at = ?
                WHERE id = ?
                """,
                (title, description, status, priority, due_date, ts, completed_at, task_id),
            )

    def delete_task(self, task_id: int) -> None:
        with get_connection() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def delete_tasks_bulk(self, task_ids: List[int]) -> int:
        if not task_ids:
            return 0

        placeholders = _build_in_clause_params(task_ids)
        sql = f"DELETE FROM tasks WHERE id IN ({placeholders})"

        with get_connection() as conn:
            cur = conn.execute(sql, task_ids)
            return cur.rowcount

    def bulk_import(self, rows: List[dict]) -> int:
        if not rows:
            return 0
        with get_connection() as conn:
            cur = conn.executemany(
                """
                INSERT INTO tasks (title, description, status, priority, due_date, created_at, updated_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        r["title"],
                        r.get("description", ""),
                        r["status"],
                        r["priority"],
                        r["due_date"],
                        r["created_at"],
                        r["updated_at"],
                        r.get("completed_at"),
                    )
                    for r in rows
                ],
            )
            return cur.rowcount

    def mark_done(self, task_id: int) -> None:
        ts = now_iso()
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET status = 'done', completed_at = COALESCE(completed_at, ?), updated_at = ?
                WHERE id = ?
                """,
                (ts, ts, task_id),
            )

    def mark_done_bulk(self, task_ids: List[int]) -> int:
        if not task_ids:
            return 0

        ts = now_iso()
        placeholders = _build_in_clause_params(task_ids)
        sql = f"""
            UPDATE tasks
            SET status = 'done', completed_at = COALESCE(completed_at, ?), updated_at = ?
            WHERE id IN ({placeholders})
        """

        with get_connection() as conn:
            cur = conn.execute(sql, [ts, ts, *task_ids])
            return cur.rowcount

    @staticmethod
    def _row_to_task(row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            priority=row["priority"],
            due_date=row["due_date"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"],
        )
