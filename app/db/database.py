import sqlite3
from datetime import datetime
from pathlib import Path


DB_DIR = Path("data")
DB_PATH = DB_DIR / "taskbook.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema_sql)


def ensure_default_prompt_template() -> None:
    template = (
        "你是一个任务管理助手。请根据给定任务列表生成今日工作日报。\n"
        "要求：\n"
        "1. 先写‘今日完成’\n"
        "2. 再写‘进行中’\n"
        "3. 再写‘明日计划’\n"
        "4. 最后写‘风险与阻塞’\n"
        "5. 使用简洁中文，分点输出\n\n"
        "日期：{date}\n"
        "任务列表：\n{tasks}\n"
    )

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM prompt_templates WHERE scene = 'daily_report' AND is_active = 1 LIMIT 1"
        ).fetchone()
        if row is None:
            conn.execute(
                """
                INSERT INTO prompt_templates (scene, name, template_text, is_active, created_at, updated_at)
                VALUES ('daily_report', '默认日报模板', ?, 1, ?, ?)
                """,
                (template, ts, ts),
            )
