from pynput.mouse import Button, Controller
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from Utils.paths import asset_path
from Workers.FrameReceiver import DISPLAY_WIDTH
from Workers.FrameSender import FrameSenderWorker


class NotifyScreen(QWidget):
    session_ended = Signal()

    def __init__(self, peer, who_is_controlling, screen_sizeX):
        super().__init__()
        self.peer = peer
        self.whoIs = who_is_controlling
        self.screen_sizeX = screen_sizeX
        # pynput cagrilari anlik oldugundan runnable/threadpool gerekmez
        self._mouse = Controller()
        self.setupUi()
        self.startSendingFrames()
        # Karsi taraftan gelen mouse olaylari bu makinede uygulanir
        self.peer.mouse_move_received.connect(self.moveMousePointer)
        self.peer.mouse_left_received.connect(self.mouseLeftClick)
        self.peer.mouse_right_received.connect(self.mouseRightClick)

    def startSendingFrames(self):
        self.thread_frame_sender = QThread()
        self.frame_sender_worker = FrameSenderWorker(self.peer)
        self.frame_sender_worker.moveToThread(self.thread_frame_sender)
        self.thread_frame_sender.started.connect(self.frame_sender_worker.run)
        self.thread_frame_sender.start()

    def setupUi(self):
        general_layout = QVBoxLayout()
        h1box = QHBoxLayout()
        h1box.addWidget(QLabel(f" {self.whoIs}  bilgisayarinizi yonetiyor..."))
        h2box = QHBoxLayout()
        exitBtn = QPushButton("Kapat", self)
        exitBtn.clicked.connect(lambda: self.session_ended.emit())
        exitBtn.setIcon(QIcon(asset_path("cancel.png")))
        h2box.addStretch()
        h2box.addWidget(exitBtn)
        h2box.addStretch()
        general_layout.addLayout(h1box)
        general_layout.addLayout(h2box)
        self.setLayout(general_layout)

    def moveMousePointer(self, x, y):
        # Karsi ekranda 1280 genislikte gosterilen frame'in koordinatlari
        # bu ekranin gercek cozunurlugune olceklenir
        rate = self.screen_sizeX / DISPLAY_WIDTH
        self._mouse.position = (x * rate, y * rate)

    def mouseLeftClick(self):
        self._mouse.click(Button.left, 1)

    def mouseRightClick(self):
        self._mouse.click(Button.right, 1)

    def stop(self):
        self.peer.mouse_move_received.disconnect(self.moveMousePointer)
        self.peer.mouse_left_received.disconnect(self.mouseLeftClick)
        self.peer.mouse_right_received.disconnect(self.mouseRightClick)
        # flag kapaninca yakalama dongusu biter; soket zaten kapali oldugundan
        # bloklanmis bir sendall varsa da hatayla cozulur
        self.frame_sender_worker.flag = False
        self.thread_frame_sender.quit()
        self.thread_frame_sender.wait(2000)
