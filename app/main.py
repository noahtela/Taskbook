import sys

from PySide6.QtWidgets import QApplication

from app.db.database import ensure_default_prompt_template, init_db
from app.ui.main_window import MainWindow
from app.utils.single_instance import SingleInstanceManager


INSTANCE_NAME = "taskbook_single_instance"


def run():
    init_db()
    ensure_default_prompt_template()
    app = QApplication(sys.argv)

    single = SingleInstanceManager(INSTANCE_NAME, app)
    if single.is_secondary_launch:
        # 已有实例在运行，发送唤起请求后直接退出
        sys.exit(0)

    win = MainWindow()
    single.raise_requested.connect(win.restore_from_tray)
    win.show()
    sys.exit(app.exec())
