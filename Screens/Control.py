from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from Workers.SendMouseLeftClick import SendMouseLeftClick
from Workers.SendMouseRightClick import SendMouseRightClick
from Workers.SendPointerPosition import SendPointerPosition

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
        self.thread5 = QThread()
        # Step 3: Create a worker object
        self.send_mouse_left_click = SendMouseRightClick(self.id, self.i_am_controlling)
        # Step 4: Move worker to the thread
        self.send_mouse_left_click.moveToThread(self.thread5)
        # Step 5: Connect signals and slots
        self.thread5.started.connect(self.send_mouse_left_click.run)
        self.send_mouse_left_click.finished.connect(self.thread5.quit)
        self.send_mouse_left_click.finished.connect(
            self.send_mouse_left_click.deleteLater
        )
        self.thread5.finished.connect(self.thread5.deleteLater)
        # Step 6: Start the thread
        self.thread5.start()

    def mouse_right_clicked(self):
        logging.info("SAG TIK ALINDI!")
        # Step 2: Create a QThread object
        self.thread4 = QThread()
        # Step 3: Create a worker object
        self.send_mouse_right_click = SendMouseRightClick(
            self.id, self.i_am_controlling
        )
        # Step 4: Move worker to the thread
        self.send_mouse_right_click.moveToThread(self.thread4)
        # Step 5: Connect signals and slots
        self.thread4.started.connect(self.send_mouse_right_click.run)
        self.send_mouse_right_click.finished.connect(self.thread4.quit)
        self.send_mouse_right_click.finished.connect(
            self.send_mouse_right_click.deleteLater
        )
        self.thread4.finished.connect(self.thread4.deleteLater)
        # Step 6: Start the thread
        self.thread4.start()

    @pyqtSlot(QPoint)
    def on_positionChanged(self, pos):
        logging.info(f"Mouse konumu => X:{pos.x()} Y:{pos.y()}")
        self.thread6 = QThread()
        # Step 3: Create a worker object
        self.send_pointer_pos_worker= SendPointerPosition(
            self.id, self.i_am_controlling, pos.x(), pos.y()
        )
        # Step 4: Move worker to the thread
        self.send_pointer_pos_worker.moveToThread(self.thread6)
        # Step 5: Connect signals and slots
        self.thread6.started.connect(self.send_pointer_pos_worker.run)
        self.send_pointer_pos_worker.finished.connect(self.thread6.quit)
        self.send_pointer_pos_worker.finished.connect(
            self.send_pointer_pos_worker.deleteLater
        )
        self.thread6.finished.connect(self.thread6.deleteLater)
        # Step 6: Start the thread
        self.thread6.start()

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