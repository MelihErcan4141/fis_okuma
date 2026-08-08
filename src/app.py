import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services.receipt_processor import ReceiptProcessor


SAFE_STATUSES = {
    "VERIFIED",
    "VERIFIED_WITH_OCR",
    "VERIFIED_WITH_AI",
    "NOT_PRESENT",
}


class ReceiptReaderApp(QMainWindow):

    def __init__(self):
        super().__init__()

        self.selected_image_path = None
        self.processor = ReceiptProcessor()

        self.setWindowTitle("ReceiptReader")
        self.resize(1000, 700)

        title = QLabel("ReceiptReader")
        title.setStyleSheet(
            "font-size: 28px; font-weight: bold;"
        )

        description = QLabel(
            "Fişlerinizi otomatik olarak okuyun ve doğrulayın."
        )

        self.image_label = QLabel(
            "Henüz fiş seçilmedi."
        )

        self.image_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.image_label.setMinimumHeight(350)

        self.image_label.setStyleSheet(
            """
            QLabel {
                border: 2px dashed #999;
                border-radius: 10px;
                padding: 10px;
            }
            """
        )

        self.select_button = QPushButton(
            "Fiş Seç"
        )

        self.select_button.setMinimumHeight(45)

        self.select_button.clicked.connect(
            self.select_receipt
        )

        self.process_button = QPushButton(
            "Fişi İşle"
        )

        self.process_button.setMinimumHeight(45)
        self.process_button.setEnabled(False)

        self.process_button.clicked.connect(
            self.process_receipt
        )

        self.status_label = QLabel(
            "Bir fiş seçerek başlayın."
        )

        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.status_label.setStyleSheet(
            "font-size: 16px;"
        )

        self.company_value = QLabel("-")
        self.receipt_no_value = QLabel("-")
        self.date_value = QLabel("-")
        self.time_value = QLabel("-")
        self.kdv_value = QLabel("-")
        self.total_value = QLabel("-")

        result_layout = QGridLayout()

        result_layout.addWidget(
            QLabel("<b>Firma</b>"),
            0,
            0
        )
        result_layout.addWidget(
            self.company_value,
            0,
            1
        )

        result_layout.addWidget(
            QLabel("<b>Fiş No</b>"),
            1,
            0
        )
        result_layout.addWidget(
            self.receipt_no_value,
            1,
            1
        )

        result_layout.addWidget(
            QLabel("<b>Tarih</b>"),
            2,
            0
        )
        result_layout.addWidget(
            self.date_value,
            2,
            1
        )

        result_layout.addWidget(
            QLabel("<b>Saat</b>"),
            3,
            0
        )
        result_layout.addWidget(
            self.time_value,
            3,
            1
        )

        result_layout.addWidget(
            QLabel("<b>KDV</b>"),
            4,
            0
        )
        result_layout.addWidget(
            self.kdv_value,
            4,
            1
        )

        result_layout.addWidget(
            QLabel("<b>Toplam</b>"),
            5,
            0
        )
        result_layout.addWidget(
            self.total_value,
            5,
            1
        )

        layout = QVBoxLayout()

        layout.addWidget(title)
        layout.addWidget(description)

        layout.addWidget(
            self.image_label
        )

        layout.addWidget(
            self.select_button
        )

        layout.addWidget(
            self.process_button
        )

        layout.addSpacing(15)

        layout.addLayout(
            result_layout
        )

        layout.addSpacing(15)

        layout.addWidget(
            self.status_label
        )

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(
            container
        )

    def select_receipt(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Fiş Seç",
            "",
            (
                "Görsel Dosyaları "
                "(*.jpg *.jpeg *.png)"
            )
        )

        if not file_path:
            return

        self.selected_image_path = file_path

        pixmap = QPixmap(
            file_path
        )

        if pixmap.isNull():
            QMessageBox.warning(
                self,
                "Hata",
                "Görsel yüklenemedi."
            )
            return

        scaled_pixmap = pixmap.scaled(
            750,
            350,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.image_label.setPixmap(
            scaled_pixmap
        )

        self.process_button.setEnabled(
            True
        )

        self.status_label.setText(
            "Fiş hazır. İşlemek için butona basın."
        )

    def process_receipt(self):
        if not self.selected_image_path:
            return

        self.process_button.setEnabled(
            False
        )

        self.status_label.setText(
            "Fiş işleniyor..."
        )

        QApplication.processEvents()

        try:
            result = self.processor.process(
                self.selected_image_path
            )

            receipt = result.receipt

            self.company_value.setText(
                self.display_value(
                    receipt.company
                )
            )

            self.receipt_no_value.setText(
                self.display_value(
                    receipt.receipt_no
                )
            )

            self.date_value.setText(
                self.display_value(
                    receipt.date
                )
            )

            self.time_value.setText(
                self.display_value(
                    receipt.time
                )
            )

            self.kdv_value.setText(
                self.display_value(
                    receipt.kdv
                )
            )

            self.total_value.setText(
                self.display_value(
                    receipt.total
                )
            )

            if result.requires_review:
                problem_fields = []

                for field in result.fields:
                    if (
                        field.status.value
                        not in SAFE_STATUSES
                    ):
                        problem_fields.append(
                            field.field_name
                        )

                text = (
                    "Kullanıcı kontrolü gerekiyor"
                )

                if problem_fields:
                    text += (
                        ": "
                        + ", ".join(
                            problem_fields
                        )
                    )

                self.status_label.setText(
                    text
                )

                self.status_label.setStyleSheet(
                    """
                    QLabel {
                        font-size: 16px;
                        font-weight: bold;
                        color: #b26a00;
                    }
                    """
                )

            else:
                self.status_label.setText(
                    "Fiş tamamen doğrulandı."
                )

                self.status_label.setStyleSheet(
                    """
                    QLabel {
                        font-size: 16px;
                        font-weight: bold;
                        color: #167c3a;
                    }
                    """
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "İşleme Hatası",
                str(error)
            )

            self.status_label.setText(
                "Fiş işlenemedi."
            )

        finally:
            self.process_button.setEnabled(
                True
            )

    @staticmethod
    def display_value(value):
        if value is None:
            return "-"

        if isinstance(
            value,
            float
        ):
            return f"{value:.2f}"

        return str(value)


def main():
    app = QApplication(
        sys.argv
    )

    window = ReceiptReaderApp()
    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()