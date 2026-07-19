from PySide6.QtCore import QPoint, Qt, QThread, Signal, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QWidget

from Workers.FrameReceiver import FrameReceiverWorker


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

    def __init__(self, peer):
        super().__init__()
        self.peer = peer
        self.setupUi()
        # Kontrol islemi baslatilir: frame'ler alinir, mouse olaylari gonderilir
        self.startFrameReceiver()

    def setupUi(self):
        self.image_frame_label = HostScreen()
        self.image_frame_label.setMaximumSize(1280, 720)
        # Mouse olaylari kucuk mesajlardir, dogrudan soketten gonderilir
        self.image_frame_label.clicked.connect(lambda: self.peer.send_mouse_left())
        self.image_frame_label.right_clicked.connect(
            lambda: self.peer.send_mouse_right()
        )
        self.image_frame_label.moved.connect(self.on_positionChanged)

        self.end_connection_btn = QPushButton("Bağlantıyı Sonlandır")
        self.end_connection_btn.clicked.connect(lambda: self.session_ended.emit())

        grid = QGridLayout()
        grid.addWidget(self.image_frame_label)
        grid.addWidget(self.end_connection_btn)
        self.setLayout(grid)

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
        try:
            self.peer.frame_received.disconnect(self.frame_receiver_worker.on_frame)
        except (TypeError, RuntimeError):
            pass  # zaten kopmus
        self.frame_receiver_thread.quit()
        self.frame_receiver_thread.wait(1000)
