from Workers.FrameSender import FrameSenderWorker

from Workers.MouseLeftClick import MouseLeftClick
from Workers.MouseRightClick import MouseRightClick
from Workers.MoveMouseCursor import MoveMouseCursor

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


import os


class NotifyScreen(QWidget):
    backtoMain = pyqtSignal()

    def __init__(self, id, who_is_controlling, screen_sizeX):
        super().__init__()
        self.id = id
        self.whoIs = who_is_controlling
        self.screen_sizeX = screen_sizeX
        self.setupUi()
        self.startSendingFrames()

    def startSendingFrames(self):
        # Step 2: Create a QThread object
        self.thread_frame_sender = QThread()
        # Step 3: Create a worker object
        self.frame_sender_worker = FrameSenderWorker(self.id, self.whoIs)
        # Step 4: Move worker to the thread
        self.frame_sender_worker.moveToThread(self.thread_frame_sender)
        # Step 5: Connect signals and slots
        self.thread_frame_sender.started.connect(self.frame_sender_worker.run)
        # Step 6: Start the thread
        self.thread_frame_sender.start()

    def setupUi(self):
        general_layout = QVBoxLayout()
        h1box = QHBoxLayout()
        h1box.addWidget(QLabel(f" {self.whoIs}  bilgisayarinizi yonetiyor..."))
        h2box = QHBoxLayout()
        exitBtn = QPushButton("Kapat", self)
        exitBtn.clicked.connect(self.closeNotify)
        exitBtn.setIcon(QIcon(f"{os.getcwd()}/assets/cancel.png"))
        h2box.addStretch()
        h2box.addWidget(exitBtn)
        h2box.addStretch()
        general_layout.addLayout(h1box)
        general_layout.addLayout(h2box)
        self.setLayout(general_layout)

    def moveMousePointer(self, x, y):
        rate = self.screen_sizeX / 1280
        x_rate = float(x) * rate
        y_rate = float(y) * rate
        # Step 2: Create a QThread object
        self.thread1 = QThread()
        # Step 3: Create a worker object
        self.move_mouse_worker = MoveMouseCursor(x_rate, y_rate)
        # Step 4: Move worker to the thread
        self.move_mouse_worker.moveToThread(self.thread1)
        # Step 5: Connect signals and slots
        self.thread1.started.connect(self.move_mouse_worker.run)
        self.move_mouse_worker.finished.connect(self.thread1.quit)
        self.move_mouse_worker.finished.connect(self.move_mouse_worker.deleteLater)
        self.thread1.finished.connect(self.thread1.deleteLater)
        self.thread1.start()

    def mouseLeftClick(self):
        # Step 2: Create a QThread object
        self.thread2 = QThread()
        # Step 3: Create a worker object
        self.mouse_left_worker = MouseLeftClick()
        # Step 4: Move worker to the thread
        self.mouse_left_worker.moveToThread(self.thread2)
        # Step 5: Connect signals and slots
        self.thread2.started.connect(self.mouse_left_worker.run)
        self.mouse_left_worker.finished.connect(self.thread2.quit)
        self.mouse_left_worker.finished.connect(self.mouse_left_worker.deleteLater)
        self.thread2.finished.connect(self.thread2.deleteLater)
        # Step 6: Start the thread
        self.thread2.start()

    def mouseRightClick(self):
        # Step 2: Create a QThread object
        self.thread3 = QThread()
        # Step 3: Create a worker object
        self.mouse_right_worker = MouseLeftClick()
        # Step 4: Move worker to the thread
        self.mouse_right_worker.moveToThread(self.thread3)
        # Step 5: Connect signals and slots
        self.thread3.started.connect(self.mouse_right_worker.run)
        self.mouse_right_worker.finished.connect(self.thread3.quit)
        self.mouse_right_worker.finished.connect(self.mouse_right_worker.deleteLater)
        self.thread3.finished.connect(self.thread3.deleteLater)
        # Step 6: Start the thread
        self.thread3.start()

    def closeNotify(self):
        self.frame_sender_worker.flag = False
        self.close()
