from typing import Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from app.repositories.prompt_template_repository import PromptTemplateRepository


DEFAULT_TEMPLATE = (
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


class PromptConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Prompt配置")
        self.resize(700, 520)

        self.scene = "daily_report"
        self.repo = PromptTemplateRepository()
        self.current_template_id: Optional[int] = None

        root_layout = QVBoxLayout(self)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("模板："))
        self.template_selector = QComboBox()
        top_row.addWidget(self.template_selector, 1)
        root_layout.addLayout(top_row)

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.template_edit = QPlainTextEdit()
        self.is_active_check = QCheckBox("设为当前启用模板")

        form.addRow("模板名称*", self.name_edit)
        form.addRow("模板内容*", self.template_edit)
        form.addRow("", self.is_active_check)
        root_layout.addLayout(form)

        tip = QLabel("可用占位符：{date}、{tasks}")
        root_layout.addWidget(tip)

        btn_row = QHBoxLayout()
        self.btn_save = QPushButton("保存")
        self.btn_close = QPushButton("关闭")
        btn_row.addStretch()
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_close)
        root_layout.addLayout(btn_row)

        self.template_selector.currentIndexChanged.connect(self._load_selected)
        self.btn_save.clicked.connect(self._save)
        self.btn_close.clicked.connect(self.reject)

        self._load_templates()

    def _load_templates(self, selected_id: Optional[int] = None):
        rows = self.repo.list_templates(scene=self.scene)

        self.template_selector.blockSignals(True)
        self.template_selector.clear()
        self.template_selector.addItem("新建模板", None)

        target_id = selected_id if selected_id is not None else self.current_template_id
        target_index = 0

        for i, row in enumerate(rows, start=1):
            label = row["name"]
            if row.get("is_active"):
                label += " (当前)"
            self.template_selector.addItem(label, row["id"])
            if target_id is not None and row["id"] == target_id:
                target_index = i

        self.template_selector.setCurrentIndex(target_index)
        self.template_selector.blockSignals(False)
        self._load_selected()

    def _reset_form(self):
        self.current_template_id = None
        self.name_edit.setText("日报模板")
        self.template_edit.setPlainText(DEFAULT_TEMPLATE)
        self.is_active_check.setChecked(False)

    def _load_selected(self):
        template_id = self.template_selector.currentData()
        if template_id is None:
            self._reset_form()
            return

        row = self.repo.get_template_by_id(int(template_id))
        if row is None:
            self._reset_form()
            return

        self.current_template_id = int(row["id"])
        self.name_edit.setText(str(row["name"]))
        self.template_edit.setPlainText(str(row["template_text"]))
        self.is_active_check.setChecked(bool(row.get("is_active")))

    def _save(self):
        name = self.name_edit.text().strip()
        template_text = self.template_edit.toPlainText().strip()

        if not name or not template_text:
            QMessageBox.warning(self, "提示", "模板名称和模板内容不能为空")
            return

        template_id = self.repo.save_template(
            scene=self.scene,
            name=name,
            template_text=template_text,
            is_active=self.is_active_check.isChecked(),
            template_id=self.current_template_id,
        )

        self.current_template_id = int(template_id)
        self._load_templates(selected_id=self.current_template_id)
        QMessageBox.information(self, "完成", "Prompt 模板已保存")
