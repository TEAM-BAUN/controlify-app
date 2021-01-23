from Threads.MouseRightClick import MouseRightClick
from Threads.MouseLeftClick import MouseLeftClick
from Threads.MoveMouseCursor import MoveMouseCursorThread
from Workers.FrameSender import FrameSenderWorker
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
        # 2. Instantiate the subclass of QRunnable
        self.move_mouse_thread = MoveMouseCursorThread(x_rate, y_rate)
        self.move_mouse_thread.start()

    def mouseLeftClick(self):
        self.mouse_left_thread = MouseLeftClick()
        self.mouse_left_thread.start()

    def mouseRightClick(self):
        self.mouse_right_thread = MouseRightClick()
        self.mouse_right_thread.start()

    def closeNotify(self):
        self.frame_sender_worker.flag = False
        self.close()
