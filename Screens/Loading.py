from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QMovie
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from Screens import theme
from Utils.paths import asset_path


class LoadingScreen(QWidget):
    # Iptal edilen bekleyisin hedef ID'sini tasir
    canceled = Signal(str)

    def __init__(self):
        super().__init__()
        self.setupUi()

    def setupUi(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        # Custom QWidget zemininin QSS ile boyanabilmesi icin sart
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("loadingScreen")
        self.setFixedWidth(340)

        self.movie = QMovie(asset_path("spinner.gif"))
        self.movie.setScaledSize(QSize(36, 36))
        self.label_animation = QLabel(self)
        self.label_animation.setMovie(self.movie)

        self.title_label = QLabel("Yanıt bekleniyor", self)
        self.title_label.setObjectName("loadingTitle")

        # Hedef ID startAnimation icinde yazilir
        self.target_id_label = QLabel(self)
        self.target_id_label.setObjectName("loadingTargetId")

        self.hint_label = QLabel("Bağlantı isteği gönderildi", self)
        self.hint_label.setObjectName("loadingHint")

        self.cancel_button = QPushButton("İptal Et", self)
        self.cancel_button.setObjectName("loadingCancel")
        self.cancel_button.setProperty("variant", "ghost")
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.clicked.connect(self.stopAnimation)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 26, 24, 26)
        layout.setSpacing(14)
        for w in (
            self.label_animation,
            self.title_label,
            self.target_id_label,
            self.hint_label,
            self.cancel_button,
        ):
            layout.addWidget(w, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.setStyleSheet(f"""
            #loadingScreen {{
                background-color: {theme.SURFACE};
            }}
            #loadingTitle {{
                color: {theme.TEXT};
                font-size: 14px; /* 13.5 yukari yuvarlandi */
                font-weight: 600;
            }}
            #loadingTargetId {{
                color: {theme.MUTED};
                font-family: {theme.MONO};
                font-size: 12px;
            }}
            #loadingHint {{
                color: {theme.FAINT};
                font-size: 11px;
            }}
            #loadingCancel {{
                padding: 7px 22px;
            }}
        """)

    def startAnimation(self, ID):
        self.id = ID
        self.target_id_label.setText(str(ID))
        self.show()
        self.movie.start()

    def stopAnimation(self):
        # Karsi tarafa vazgectigimizi baglantiyi kapatarak bildiririz;
        # durum sifirlama ve ana ekrana donus Main tarafinda yapilir
        self.canceled.emit(self.id)
        self.close()

    def closeEvent(self, event):
        # Pencere hangi yoldan kapanirsa kapansin animasyon durur
        self.movie.stop()
        event.accept()
