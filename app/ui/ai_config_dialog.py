from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from app.repositories.ai_model_config_repository import AIModelConfigRepository


class AIConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI模型配置")
        self.resize(560, 360)

        self.repo = AIModelConfigRepository()
        self.current_config_id: Optional[int] = None

        root_layout = QVBoxLayout(self)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("配置："))
        self.config_selector = QComboBox()
        top_row.addWidget(self.config_selector, 1)
        root_layout.addLayout(top_row)

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.base_url_edit = QLineEdit()
        self.model_edit = QLineEdit()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)

        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(0.7)

        self.use_max_tokens = QCheckBox("限制 max_tokens")
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 128000)
        self.max_tokens_spin.setValue(2048)
        self.max_tokens_spin.setEnabled(False)

        self.is_active_check = QCheckBox("设为当前启用配置")

        self.use_max_tokens.toggled.connect(self.max_tokens_spin.setEnabled)

        form.addRow("名称*", self.name_edit)
        form.addRow("Base URL*", self.base_url_edit)
        form.addRow("Model*", self.model_edit)
        form.addRow("API Key*", self.api_key_edit)
        form.addRow("Temperature", self.temperature_spin)
        form.addRow(self.use_max_tokens, self.max_tokens_spin)
        form.addRow("", self.is_active_check)
        root_layout.addLayout(form)

        tip = QLabel("提示：建议使用 HTTPS 地址，API Key 仅保存在本地数据库。")
        tip.setAlignment(Qt.AlignLeft)
        root_layout.addWidget(tip)

        btn_row = QHBoxLayout()
        self.btn_save = QPushButton("保存")
        self.btn_close = QPushButton("关闭")
        btn_row.addStretch()
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_close)
        root_layout.addLayout(btn_row)

        self.config_selector.currentIndexChanged.connect(self._load_selected)
        self.btn_save.clicked.connect(self._save)
        self.btn_close.clicked.connect(self.reject)

        self._load_configs()

    def _load_configs(self, selected_id: Optional[int] = None):
        configs = self.repo.list_configs()

        self.config_selector.blockSignals(True)
        self.config_selector.clear()
        self.config_selector.addItem("新建配置", None)

        target_id = selected_id if selected_id is not None else self.current_config_id
        target_index = 0

        for i, cfg in enumerate(configs, start=1):
            label = cfg["name"]
            if cfg.get("is_active"):
                label += " (当前)"
            self.config_selector.addItem(label, cfg["id"])
            if target_id is not None and cfg["id"] == target_id:
                target_index = i

        self.config_selector.setCurrentIndex(target_index)
        self.config_selector.blockSignals(False)
        self._load_selected()

    def _reset_form(self):
        self.current_config_id = None
        self.name_edit.clear()
        self.base_url_edit.setText("https://api.openai.com/v1")
        self.model_edit.setText("gpt-4o-mini")
        self.api_key_edit.clear()
        self.temperature_spin.setValue(0.7)
        self.use_max_tokens.setChecked(False)
        self.max_tokens_spin.setValue(2048)
        self.max_tokens_spin.setEnabled(False)
        self.is_active_check.setChecked(False)

    def _load_selected(self):
        config_id = self.config_selector.currentData()
        if config_id is None:
            self._reset_form()
            return

        row = self.repo.get_config_by_id(int(config_id))
        if row is None:
            self._reset_form()
            return

        self.current_config_id = int(row["id"])
        self.name_edit.setText(str(row["name"]))
        self.base_url_edit.setText(str(row["base_url"]))
        self.model_edit.setText(str(row["model_name"]))
        self.api_key_edit.setText(str(row["api_key"]))
        self.temperature_spin.setValue(float(row.get("temperature") or 0.7))

        max_tokens = row.get("max_tokens")
        if max_tokens:
            self.use_max_tokens.setChecked(True)
            self.max_tokens_spin.setEnabled(True)
            self.max_tokens_spin.setValue(int(max_tokens))
        else:
            self.use_max_tokens.setChecked(False)
            self.max_tokens_spin.setEnabled(False)

        self.is_active_check.setChecked(bool(row.get("is_active")))

    def _save(self):
        name = self.name_edit.text().strip()
        base_url = self.base_url_edit.text().strip().rstrip("/")
        model_name = self.model_edit.text().strip()
        api_key = self.api_key_edit.text().strip()

        if not name or not base_url or not model_name or not api_key:
            QMessageBox.warning(self, "提示", "名称、Base URL、Model、API Key 不能为空")
            return

        if not base_url.startswith("https://"):
            QMessageBox.warning(self, "提示", "Base URL 必须是 HTTPS 地址")
            return

        max_tokens = self.max_tokens_spin.value() if self.use_max_tokens.isChecked() else None

        config_id = self.repo.save_config(
            name=name,
            base_url=base_url,
            model_name=model_name,
            api_key=api_key,
            temperature=float(self.temperature_spin.value()),
            max_tokens=max_tokens,
            is_active=self.is_active_check.isChecked(),
            config_id=self.current_config_id,
        )

        self.current_config_id = int(config_id)
        self._load_configs(selected_id=self.current_config_id)
        QMessageBox.information(self, "完成", "AI 模型配置已保存")
