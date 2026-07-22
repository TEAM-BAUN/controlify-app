from PySide6.QtCore import QPoint, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from Screens import theme
from Utils.workers import FrameReceiverWorker


class HostScreen(QLabel):
    """Karsi ekranin goruntusunu gosterir, uzerindeki mouse olaylarini yayar."""

    clicked = Signal()
    right_clicked = Signal()
    moved = Signal(QPoint)

    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        self.moved.emit(event.position().toPoint())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        if event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit()


class PcControlScreen(QWidget):
    session_ended = Signal()

    def __init__(self, peer, target_id):
        super().__init__()
        self.peer = peer
        self.target_id = target_id
        self.setupUi()
        # Kontrol islemi baslatilir: frame'ler alinir, mouse olaylari gonderilir
        self.startFrameReceiver()

    def setupUi(self):
        self.setWindowTitle("Controlify")
        self.setObjectName("pcControlScreen")
        # QSS zemininin boyanmasi icin sart (custom QWidget alt sinifi)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            #pcControlScreen {{
                background-color: {theme.BG};
            }}
            #topBar {{
                background-color: {theme.SURFACE};
                border: none;
                border-bottom: 1px solid {theme.BORDER};
            }}
            #statusDot {{
                background-color: {theme.GREEN};
                border-radius: 4px;
            }}
            #connectedLabel {{
                font-size: 13px;
                font-weight: 600;
            }}
            #targetIdLabel {{
                font-family: {theme.MONO};
                font-size: 12px;
                color: {theme.MUTED};
            }}
            #typeChip {{
                background-color: {theme.ACCENT_TINT};
                color: {theme.ACCENT};
                font-size: 10px;
                font-weight: 600;
                border-radius: 5px;
                padding: 3px 8px;
            }}
            #durationLabel {{
                font-family: {theme.MONO};
                font-size: 12px;
                color: {theme.FAINT};
            }}
            #frameArea {{
                background-color: {theme.FRAME_BG};
                border: 1px solid {theme.BORDER};
                border-radius: 8px;
            }}
        """)

        # Ust bar: durum noktasi, baglanti bilgisi, sure sayaci, sonlandirma
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        bar_layout = QHBoxLayout(top_bar)
        bar_layout.setContentsMargins(16, 10, 16, 10)
        bar_layout.setSpacing(10)

        status_dot = QLabel()
        status_dot.setObjectName("statusDot")
        status_dot.setFixedSize(8, 8)

        connected_label = QLabel("Bağlı")
        connected_label.setObjectName("connectedLabel")

        target_id_label = QLabel(self.target_id)
        target_id_label.setObjectName("targetIdLabel")

        type_chip = QLabel("Bilgisayar Yönetimi")
        type_chip.setObjectName("typeChip")

        self.duration_label = QLabel("00:00")
        self.duration_label.setObjectName("durationLabel")

        self.end_connection_btn = QPushButton("Bağlantıyı Sonlandır")
        self.end_connection_btn.setProperty("variant", "danger")
        self.end_connection_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.end_connection_btn.clicked.connect(self.session_ended)

        bar_layout.addWidget(status_dot)
        bar_layout.addWidget(connected_label)
        bar_layout.addWidget(target_id_label)
        bar_layout.addWidget(type_chip)
        bar_layout.addStretch()
        bar_layout.addWidget(self.duration_label)
        bar_layout.addWidget(self.end_connection_btn)

        # Sure sayaci: saniyede bir mm:ss guncellenir
        self._elapsed_seconds = 0
        self.duration_timer = QTimer(self)
        self.duration_timer.timeout.connect(self.updateDuration)
        self.duration_timer.start(1000)

        # Frame alani: HostScreen'i saran cerceve (radius/border cerceveden,
        # HostScreen'e offset eklenmez ki mouse koordinatlari bozulmasin)
        self.image_frame_label = HostScreen()
        self.image_frame_label.setMaximumSize(1280, 720)
        # Mouse olaylari kucuk mesajlardir, dogrudan soketten gonderilir
        self.image_frame_label.clicked.connect(self.peer.send_mouse_left)
        self.image_frame_label.right_clicked.connect(self.peer.send_mouse_right)
        self.image_frame_label.moved.connect(self.on_positionChanged)

        frame_area = QFrame()
        frame_area.setObjectName("frameArea")
        frame_layout = QVBoxLayout(frame_area)
        frame_layout.setContentsMargins(1, 1, 1, 1)
        frame_layout.addWidget(self.image_frame_label)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(14, 14, 14, 14)
        content_layout.addWidget(frame_area)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(top_bar)
        root_layout.addLayout(content_layout, 1)

    @Slot()
    def updateDuration(self):
        self._elapsed_seconds += 1
        minutes, seconds = divmod(self._elapsed_seconds, 60)
        self.duration_label.setText(f"{minutes:02d}:{seconds:02d}")

    @Slot(QPoint)
    def on_positionChanged(self, pos):
        self.peer.send_mouse_move(pos.x(), pos.y())

    @Slot(QImage)
    def setImage(self, image):
        self.image_frame_label.setPixmap(QPixmap.fromImage(image))

    def startFrameReceiver(self):
        # JPEG cozme islemi arayuzu dondurmamak icin ayri thread'de yapilir
        self.frame_receiver_thread = QThread()
        self.frame_receiver_worker = FrameReceiverWorker()
        self.frame_receiver_worker.moveToThread(self.frame_receiver_thread)
        self.peer.frame_received.connect(self.frame_receiver_worker.on_frame)
        self.frame_receiver_worker.changePixmap.connect(self.setImage)
        self.frame_receiver_thread.start()

    def stop(self):
        self.duration_timer.stop()
        try:
            self.peer.frame_received.disconnect(self.frame_receiver_worker.on_frame)
        except (TypeError, RuntimeError):
            pass  # zaten kopmus
        self.frame_receiver_thread.quit()
        self.frame_receiver_thread.wait(1000)
