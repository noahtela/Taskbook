from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
)


class ReportPreviewDialog(QDialog):
    def __init__(self, report_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("日报预览")
        self.resize(760, 560)

        root_layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMarkdown(report_text)
        root_layout.addWidget(self.text_edit)

        btn_row = QHBoxLayout()
        self.btn_copy = QPushButton("复制到剪贴板")
        self.btn_close = QPushButton("关闭")
        btn_row.addStretch()
        btn_row.addWidget(self.btn_copy)
        btn_row.addWidget(self.btn_close)
        root_layout.addLayout(btn_row)

        self.btn_copy.clicked.connect(self.copy_text)
        self.btn_close.clicked.connect(self.accept)

    def copy_text(self):
        QApplication.clipboard().setText(self.text_edit.toPlainText())
        QMessageBox.information(self, "完成", "日报已复制")
