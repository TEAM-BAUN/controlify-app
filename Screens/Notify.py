from Runnables.MouseRightClick import MouseRightClickRunnable
from Runnables.MouseLeftClick import MouseLeftClickRunnable
from Workers.FrameSender import FrameSenderWorker
from Runnables.MoveMouseCursor import MoveMouseCursorRunnable
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from Workers.MousePosListener import MousePosListenerWorker

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
        self.startListeningMousePositions()

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

    def startListeningMousePositions(self):
        # Step 2: Create a QThread object
        self.thread_mouse_pos_listener = QThread()
        # Step 3: Create a worker object
        self.mouse_pos_worker = MousePosListenerWorker(self.id, self.whoIs)
        self.mouse_pos_worker.mouse_pointer_pos.connect(self.moveMousePointer)
        # Step 4: Move worker to the thread
        self.mouse_pos_worker.moveToThread(self.thread_mouse_pos_listener)
        # Step 5: Connect signals and slots
        self.thread_mouse_pos_listener.started.connect(self.mouse_pos_worker.run)
        # Step 6: Start the thread
        self.thread_mouse_pos_listener.start()

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
        runnable1 = MoveMouseCursorRunnable(x_rate, y_rate)
        # 3. Call start()
        QThreadPool.globalInstance().start(runnable1)

    def mouseLeftClick(self):
        # 2. Instantiate the subclass of QRunnable
        runnable2 = MouseLeftClickRunnable()
        # 3. Call start()
        QThreadPool.globalInstance().start(runnable2)

    def mouseRightClick(self):
        # 2. Instantiate the subclass of QRunnable
        runnable3 = MouseRightClickRunnable()
        # 3. Call start()
        QThreadPool.globalInstance().start(runnable3)

    def closeNotify(self):
        self.frame_sender_worker.flag = False
        self.close()
