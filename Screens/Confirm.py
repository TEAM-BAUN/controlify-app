"""Onay/uyari dialoglari (tasarim 2d).

QMessageBox yerine koyu temali tek QDialog sinifi; uc kullanim
ask_connection / ask / warn staticmethod'lari uzerinden saglanir.
"""

import html

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from Screens import theme


class ConfirmDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        title: str,
        body: str,
        chip_text: str | None = None,
        confirm_text: str = "Tamam",
        reject_text: str | None = None,
        danger: bool = False,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(400)

        # Uyari varyantinda ikon zemini DANGER tint, digerlerinde ACCENT tint
        icon_bg = theme.DANGER_TINT if danger else theme.ACCENT_TINT
        # Yarim piksel boyutlar yukari yuvarlandi: 12.5->13, 10.5->11, 2.5->3
        self.setStyleSheet(
            f"""
            QLabel#dialogTitle {{
                font-size: 14px;
                font-weight: 600;
                color: {theme.TEXT};
            }}
            QLabel#dialogBody {{
                font-size: 13px;
                color: {theme.MUTED};
            }}
            QLabel#typeChip {{
                background-color: {theme.ACCENT_TINT};
                color: {theme.ACCENT};
                font-size: 11px;
                font-weight: 600;
                border-radius: 5px;
                padding: 3px 8px;
            }}
            QLabel#iconBox {{
                background-color: {icon_bg};
                border-radius: 10px;
            }}
            QLabel#iconRing {{
                border: 3px solid {theme.ACCENT};
                border-radius: 7px;
            }}
            QLabel#iconMark {{
                color: {theme.DANGER};
                font-size: 16px;
                font-weight: 700;
            }}
            QPushButton#confirmBtn, QPushButton#rejectBtn {{
                padding: 8px 18px;
            }}
            """
        )

        # Sol ikon: 38px kare, icinde halka (normal) ya da unlem (uyari)
        icon_box = QLabel()
        icon_box.setObjectName("iconBox")
        icon_box.setFixedSize(38, 38)
        icon_layout = QVBoxLayout(icon_box)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        if danger:
            mark = QLabel("!")
            mark.setObjectName("iconMark")
            mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_layout.addWidget(mark)
        else:
            ring = QLabel()
            ring.setObjectName("iconRing")
            ring.setFixedSize(14, 14)
            icon_layout.addWidget(ring, 0, Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setObjectName("dialogTitle")

        body_label = QLabel(body)
        body_label.setObjectName("dialogBody")
        body_label.setWordWrap(True)

        text_col = QVBoxLayout()
        text_col.setSpacing(6)
        text_col.addWidget(title_label)
        text_col.addWidget(body_label)
        if chip_text:
            chip = QLabel(chip_text)
            chip.setObjectName("typeChip")
            chip_row = QHBoxLayout()
            chip_row.addWidget(chip)
            chip_row.addStretch()
            text_col.addLayout(chip_row)

        content = QHBoxLayout()
        content.setSpacing(14)
        content.addWidget(icon_box, 0, Qt.AlignmentFlag.AlignTop)
        content.addLayout(text_col, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()
        if reject_text is not None:
            reject_btn = QPushButton(reject_text)
            reject_btn.setObjectName("rejectBtn")
            reject_btn.setProperty("variant", "ghost")
            reject_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            reject_btn.clicked.connect(self.reject)
            btn_row.addWidget(reject_btn)
        confirm_btn = QPushButton(confirm_text)
        confirm_btn.setObjectName("confirmBtn")
        confirm_btn.setProperty("variant", "primary")
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.clicked.connect(self.accept)
        btn_row.addWidget(confirm_btn)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)
        outer.addLayout(content)
        outer.addLayout(btn_row)

    @staticmethod
    def ask_connection(parent, who: str, connection_type: str) -> bool:
        # Gelen baglanti istegi: ID mono, tip chip'i, Reddet/Kabul Et
        body = (
            f'<span style="font-family: {theme.MONO}; color: {theme.TEXT};'
            f' font-weight: 500;">{html.escape(who)}</span>'
            " bilgisayarınıza bağlanmak istiyor."
        )
        dialog = ConfirmDialog(
            parent,
            "Bağlantı isteği",
            body,
            chip_text=connection_type,
            confirm_text="Kabul Et",
            reject_text="Reddet",
        )
        return dialog.exec() == QDialog.DialogCode.Accepted

    @staticmethod
    def ask(
        parent,
        title: str,
        message: str,
        confirm_text: str = "Evet",
        reject_text: str = "Vazgeç",
    ) -> bool:
        # Genel iki butonlu onay (or. cikis onayi)
        dialog = ConfirmDialog(
            parent, title, message, confirm_text=confirm_text, reject_text=reject_text
        )
        return dialog.exec() == QDialog.DialogCode.Accepted

    @staticmethod
    def warn(parent, message: str) -> None:
        # Tek butonlu uyari varyanti
        ConfirmDialog(
            parent, "Uyarı", message, confirm_text="Tamam", danger=True
        ).exec()
