from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from Runnables.SendMouseLeftClick import SendMouseLeftClickRunnable
from Runnables.SendMouseRightClick import SendMouseRightClickRunnable
from Runnables.SendPointerPosition import SendPointerPositionRunnable

from Utils.redisconn import redisServerSetup

from Workers.FrameReceiver import FrameReceiverWorker

import logging
import time

status, r, p = redisServerSetup()


class HostScreen(QLabel):
    clicked = pyqtSignal()
    right_clicked = pyqtSignal()

    def mouseReleaseEvent(self, QMouseEvent):
        # Mouse tiklamalarina gore Redis iletisimi icin tanimlanmis fonksiyonlar tetiklenir
        if QMouseEvent.button() == Qt.LeftButton:
            self.clicked.emit()
        if QMouseEvent.button() == Qt.RightButton:
            self.right_clicked.emit()


class PcControlScreen(QWidget):
    close_control_screen = pyqtSignal(str)

    def __init__(self, id, i_am_controlling):
        super().__init__()
        # Control eden PC ekrani olusurken kimi kontrol ettigi ve kendi idsinin ne oldugu belirtilir
        self.id = id
        self.i_am_controlling = i_am_controlling
        self.pool = QThreadPool()
        # Kullanilmayan processlerin zaman asimina ugrar ve silinir
        self.pool.setExpiryTimeout(100)
        self.pool.setMaxThreadCount(4)
        self.setupUi()
        # Kontrol islemi baslatilir.Frame,Mouse bilgileri alinir veya gonderilir
        self.startFrameReveiver()

    def setupUi(self):
        self.setObjectName("PC Control")

        self.image_frame_label = HostScreen()
        self.image_frame_label.setMaximumSize(1280, 720)
        self.image_frame_label.setMouseTracking(True)
        self.image_frame_label.clicked.connect(self.mouse_clicked)
        self.image_frame_label.right_clicked.connect(self.mouse_right_clicked)

        self.end_connection_btn = QPushButton("Bağlantıyı Sonlandır")
        self.end_connection_btn.clicked.connect(self.exit_from_here)

        tracker = MouseTracker(self.image_frame_label)
        # Mouse Frame'in ustunde hareket ettikce fonksiyon tetiklenir
        tracker.positionChanged.connect(self.on_positionChanged)
        self.grid = QGridLayout()
        self.grid.addWidget(self.image_frame_label)
        self.grid.addWidget(self.end_connection_btn)

        self.setLayout(self.grid)

    def exit_from_here(self):
        self.close_control_screen.emit(self.i_am_controlling)

    def mouse_clicked(self):
        logging.info("SOL TIK ALINDI!")
        # Sol tik islemi havuzdaki yerini alir ve sirasi geldiginde calisir.
        # bu islem bilgisayarin veya GUI nin kasmasini engeller
        runnable1 = SendMouseLeftClickRunnable(self.id, self.i_am_controlling)
        # 3. Call start()
        self.pool.start(runnable1)

    def mouse_right_clicked(self):
        logging.info("SAG TIK ALINDI!")
        runnable2 = SendMouseRightClickRunnable(self.id, self.i_am_controlling)
        # 3. Call start()
        self.pool.start(runnable2)

    @pyqtSlot(QPoint)
    def on_positionChanged(self, pos):
        runnable3 = SendPointerPositionRunnable(
            self.id, self.i_am_controlling, pos.x(), pos.y()
        )
        self.pool.start(runnable3)

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.image_frame_label.setPixmap(QPixmap.fromImage(image))

    def startFrameReveiver(self):
        self.frame_receiver_thread = QThread()
        self.frame_receiver_worker = FrameReceiverWorker(self.id, self.i_am_controlling)
        self.frame_receiver_worker.moveToThread(self.frame_receiver_thread)
        self.frame_receiver_thread.started.connect(self.frame_receiver_worker.run)
        self.frame_receiver_thread.start()


class MouseTracker(QObject):
    positionChanged = pyqtSignal(QPoint)

    def __init__(self, widget):
        super().__init__(widget)
        self._widget = widget
        # Mouse takibi aktiflestirimek
        self.widget.setMouseTracking(True)
        self.widget.installEventFilter(self)

    @property
    def widget(self):
        return self._widget

    def eventFilter(self, o, e):
        if o is self.widget and e.type() == QEvent.MouseMove:
            self.positionChanged.emit(e.pos())
        return super().eventFilter(o, e)
