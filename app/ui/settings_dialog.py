from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
)

from app.repositories.settings_repository import SettingsRepository


THEME_OPTIONS = [
    ("暗黑", "dark"),
    ("简白", "light"),
    ("透明", "transparent"),
]


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统设置")
        self.resize(460, 300)

        self.repo = SettingsRepository()
        self._remind_test_handler = None

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.remind_toggle = QCheckBox("启用到期提醒")

        self.remind_threshold_spin = QSpinBox()
        self.remind_threshold_spin.setRange(1, 10080)
        self.remind_threshold_spin.setSuffix(" 分钟")

        self.periodic_toggle = QCheckBox("启用定期提醒待办/进行中")
        self.periodic_minutes_spin = QSpinBox()
        self.periodic_minutes_spin.setRange(15, 10080)
        self.periodic_minutes_spin.setSuffix(" 分钟")

        self.theme_combo = QComboBox()
        for label, value in THEME_OPTIONS:
            self.theme_combo.addItem(label, value)

        alpha_row = QHBoxLayout()
        self.alpha_slider = QSlider(Qt.Horizontal)
        self.alpha_slider.setRange(50, 100)
        self.alpha_slider.setSingleStep(1)
        self.alpha_value_label = QLabel()
        alpha_row.addWidget(self.alpha_slider, 1)
        alpha_row.addWidget(self.alpha_value_label)

        form.addRow(self.remind_toggle)
        form.addRow("到期提醒阈值", self.remind_threshold_spin)
        form.addRow(self.periodic_toggle)
        form.addRow("定期提醒间隔", self.periodic_minutes_spin)
        form.addRow("主题", self.theme_combo)
        form.addRow("透明度", alpha_row)
        layout.addLayout(form)

        self.btn_test_reminder = QPushButton("立即触发一次到期提醒")
        layout.addWidget(self.btn_test_reminder)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self.alpha_slider.valueChanged.connect(self._on_alpha_changed)
        self.btn_test_reminder.clicked.connect(self._on_test_reminder_clicked)
        self.remind_toggle.stateChanged.connect(self._on_remind_toggle)
        self.periodic_toggle.stateChanged.connect(self._on_periodic_toggle)

        self._load()

    def set_reminder_test_handler(self, handler):
        self._remind_test_handler = handler

    def _load(self):
        threshold = self.repo.get("remind_threshold_minutes", "60")
        remind_enabled = self.repo.get("remind_enabled", "1")
        periodic_enabled = self.repo.get("periodic_enabled", "0")
        periodic_minutes = self.repo.get("periodic_minutes", "60")
        theme = self.repo.get("theme", "light")
        alpha = self.repo.get("transparent_alpha", "85")

        self.remind_toggle.setChecked(remind_enabled == "1")
        try:
            self.remind_threshold_spin.setValue(max(1, int(threshold)))
        except ValueError:
            self.remind_threshold_spin.setValue(60)

        self.periodic_toggle.setChecked(periodic_enabled == "1")
        try:
            self.periodic_minutes_spin.setValue(max(15, int(periodic_minutes)))
        except ValueError:
            self.periodic_minutes_spin.setValue(60)

        idx = self.theme_combo.findData(theme)
        if idx < 0:
            idx = self.theme_combo.findData("light")
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)

        try:
            self.alpha_slider.setValue(min(100, max(50, int(alpha))))
        except ValueError:
            self.alpha_slider.setValue(85)

        self._on_alpha_changed(self.alpha_slider.value())
        self._on_theme_changed(self.theme_combo.currentIndex())

    def _on_theme_changed(self, _index: int):
        theme = str(self.theme_combo.currentData())
        is_transparent = theme == "transparent"
        self.alpha_slider.setEnabled(is_transparent)

    def _on_alpha_changed(self, value: int):
        self.alpha_value_label.setText(f"{value}%")

    def _on_test_reminder_clicked(self):
        if callable(self._remind_test_handler):
            self._remind_test_handler()

    def _on_remind_toggle(self, state: int):
        enabled = state == 2
        self.remind_threshold_spin.setEnabled(enabled)
        self.btn_test_reminder.setEnabled(enabled)

    def _on_periodic_toggle(self, state: int):
        enabled = state == 2
        self.periodic_minutes_spin.setEnabled(enabled)

    def save(self):
        self.repo.set("remind_enabled", "1" if self.remind_toggle.isChecked() else "0")
        self.repo.set("remind_threshold_minutes", str(self.remind_threshold_spin.value()))
        self.repo.set("periodic_enabled", "1" if self.periodic_toggle.isChecked() else "0")
        self.repo.set("periodic_minutes", str(self.periodic_minutes_spin.value()))
        self.repo.set("theme", str(self.theme_combo.currentData()))
        self.repo.set("transparent_alpha", str(self.alpha_slider.value()))

    def get_values(self):
        return {
            "remind_enabled": self.remind_toggle.isChecked(),
            "remind_threshold_minutes": self.remind_threshold_spin.value(),
            "periodic_enabled": self.periodic_toggle.isChecked(),
            "periodic_minutes": self.periodic_minutes_spin.value(),
            "theme": str(self.theme_combo.currentData()),
            "transparent_alpha": self.alpha_slider.value(),
        }
