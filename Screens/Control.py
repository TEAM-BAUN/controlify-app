from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from Runnables.SendMouseLeftClick import SendMouseLeftClickRunnable
from Runnables.SendMouseRightClick import SendMouseRightClickRunnable
from Runnables.SendPointerPosition import SendPointerPositionRunnable

from Utils.redisconn import redisServerSetup

from Workers.FrameReceiver import FrameReceiverWorker

import logging

status, r, p = redisServerSetup()


class HostScreen(QLabel):
    clicked = pyqtSignal()
    right_clicked = pyqtSignal()

    def mouseReleaseEvent(self, QMouseEvent):
        if QMouseEvent.button() == Qt.LeftButton:
            self.clicked.emit()
        if QMouseEvent.button() == Qt.RightButton:
            self.right_clicked.emit()


class PcControlScreen(QWidget):
    close_control_screen = pyqtSignal(str)

    def __init__(self, id, i_am_controlling):
        super().__init__()
        self.id = id
        self.i_am_controlling = i_am_controlling
        self.setupUi()
        self.startFrameReveiver()

    def setupUi(self):
        self.setObjectName("PC Control")
        # self.setMaximumSize(1280, 720)
        self.image_frame_label = HostScreen()
        self.image_frame_label.setMaximumSize(1280, 720)
        self.image_frame_label.setMouseTracking(True)
        self.image_frame_label.clicked.connect(self.mouse_clicked)
        self.image_frame_label.right_clicked.connect(self.mouse_right_clicked)

        self.end_connection_btn = QPushButton("Bağlantıyı Sonlandır")
        self.end_connection_btn.clicked.connect(self.exit_from_here)

        tracker = MouseTracker(self.image_frame_label)
        tracker.positionChanged.connect(self.on_positionChanged)
        self.grid = QGridLayout()
        self.grid.addWidget(self.image_frame_label)
        self.grid.addWidget(self.end_connection_btn)
        # self.grid.addWidget(self.close_btn)
        self.setLayout(self.grid)

    def exit_from_here(self):
        self.close_control_screen.emit(self.i_am_controlling)

    def mouse_clicked(self):
        logging.info("SOL TIK ALINDI!")
        pool = QThreadPool.globalInstance()
        runnable = SendMouseLeftClickRunnable(self.id, self.i_am_controlling)
        # 3. Call start()
        pool.start(runnable)

    def mouse_right_clicked(self):
        logging.info("SAG TIK ALINDI!")
        pool = QThreadPool.globalInstance()
        runnable = SendMouseRightClickRunnable(self.id, self.i_am_controlling)
        # 3. Call start()
        pool.start(runnable)

    @pyqtSlot(QPoint)
    def on_positionChanged(self, pos):
        logging.info(f"Mouse konumu => X:{pos.x()} Y:{pos.y()}")
        pool = QThreadPool.globalInstance()
        runnable = SendPointerPositionRunnable(
            self.id, self.i_am_controlling, pos.x(), pos.y()
        )
        # 3. Call start()
        pool.start(runnable)

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.image_frame_label.setPixmap(QPixmap.fromImage(image))

    def startFrameReveiver(self):
        # Step 2: Create a QThread object
        self.frame_receiver_thread = QThread()
        # Step 3: Create a worker object
        self.frame_receiver_worker = FrameReceiverWorker(self.id, self.i_am_controlling)
        # Step 4: Move worker to the thread
        self.frame_receiver_worker.moveToThread(self.frame_receiver_thread)
        # Step 5: Connect signals and slots
        self.frame_receiver_thread.started.connect(self.frame_receiver_worker.run)
        # self.frame_receiver_worker.finished.connect(self.frame_receiver_thread.quit)
        # self.frame_receiver_worker.finished.connect(
        #     self.frame_receiver_worker.deleteLater
        # )
        # self.frame_receiver_thread.finished.connect(
        #     self.frame_receiver_thread.deleteLater
        # )
        self.frame_receiver_worker.changePixmap.connect(self.setImage)
        # Step 6: Start the thread
        self.frame_receiver_thread.start()


class MouseTracker(QObject):
    positionChanged = pyqtSignal(QPoint)

    def __init__(self, widget):
        super().__init__(widget)
        self._widget = widget
        self.widget.setMouseTracking(True)
        self.widget.installEventFilter(self)

    @property
    def widget(self):
        return self._widget

    def eventFilter(self, o, e):
        if o is self.widget and e.type() == QEvent.MouseMove:
            self.positionChanged.emit(e.pos())
        return super().eventFilter(o, e)