from datetime import datetime, timedelta
from typing import Optional

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QDateTimeEdit,
)

from app.models.task import Task


class TaskDialog(QDialog):
    def __init__(self, parent=None, task: Optional[Task] = None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle("编辑任务" if task else "新建任务")
        self.resize(460, 320)
        self._confirmed_close = False

        self.title_edit = QLineEdit()
        self.desc_edit = QTextEdit()

        self.status_combo = QComboBox()
        self.status_combo.addItem("待办(todo)", "todo")
        self.status_combo.addItem("进行中(doing)", "doing")
        self.status_combo.addItem("已完成(done)", "done")

        self.priority_combo = QComboBox()
        self.priority_combo.addItem("高(1)", 1)
        self.priority_combo.addItem("中(2)", 2)
        self.priority_combo.addItem("低(3)", 3)

        self.has_due_date = QCheckBox("截止时间(必填)")
        self.due_date_edit = QDateTimeEdit()
        self.due_date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.due_date_edit.setCalendarPopup(True)
        self._set_default_due_datetime()
        self.has_due_date.setChecked(True)
        self.has_due_date.setEnabled(False)
        self.due_date_edit.setEnabled(True)

        form = QFormLayout(self)
        form.addRow("标题*", self.title_edit)
        form.addRow("描述", self.desc_edit)
        form.addRow("状态", self.status_combo)
        form.addRow("优先级", self.priority_combo)
        form.addRow(self.has_due_date, self.due_date_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self._confirm_reject)
        form.addRow(buttons)

        if task is not None:
            self._load_task(task)
        else:
            self._set_default_values()

    def _set_default_values(self):
        self.status_combo.setCurrentIndex(0)
        self.priority_combo.setCurrentIndex(1)
        self._set_default_due_datetime()

    def _set_default_due_datetime(self):
        now = datetime.now()
        target = now.replace(hour=18, minute=0, second=0, microsecond=0)
        if now >= target:
            target = target + timedelta(days=1)
        self.has_due_date.setChecked(True)
        self.due_date_edit.setEnabled(True)
        self.due_date_edit.setDateTime(QDateTime(target))

    def _confirm_reject(self):
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "确认",
            "确定要关闭吗？未保存的内容将丢失。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._confirmed_close = True
            self.reject()

    def _on_accept(self):
        data = self.get_data()
        if data is None:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "提示", "截止时间为必填，请设置截止时间")
            return
        self.accept()

    def reject(self):
        if self._confirmed_close:
            super().reject()
            return
        self._confirm_reject()

    def _load_task(self, task: Task):
        self.title_edit.setText(task.title)
        self.desc_edit.setPlainText(task.description or "")

        status_idx = self.status_combo.findData(task.status)
        if status_idx >= 0:
            self.status_combo.setCurrentIndex(status_idx)

        priority_idx = self.priority_combo.findData(task.priority)
        if priority_idx >= 0:
            self.priority_combo.setCurrentIndex(priority_idx)

        if task.due_date:
            dt = QDateTime.fromString(task.due_date, "yyyy-MM-dd HH:mm:ss")
            if not dt.isValid():
                dt = QDateTime.fromString(task.due_date, "yyyy-MM-dd HH:mm")
            if dt.isValid():
                self.has_due_date.setChecked(True)
                self.due_date_edit.setEnabled(True)
                self.due_date_edit.setDateTime(dt)

    def get_data(self):
        title = self.title_edit.text().strip()
        description = self.desc_edit.toPlainText().strip()
        status = self.status_combo.currentData()
        priority = int(self.priority_combo.currentData())

        due_date = None
        if self.has_due_date.isChecked():
            due_date = self.due_date_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")

        if not due_date:
            return None

        return {
            "title": title,
            "description": description,
            "status": status,
            "priority": priority,
            "due_date": due_date,
        }
