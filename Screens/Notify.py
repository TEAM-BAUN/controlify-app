from pynput.mouse import Button, Controller
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from Screens import theme
from Utils.workers import DISPLAY_WIDTH, FrameSenderWorker


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
        self.setWindowTitle("Controlify — Uzaktan Yönetim")
        self.setFixedWidth(420)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setObjectName("notifyRoot")
        # Ozel QWidget zemininin QSS ile boyanabilmesi icin sart
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QWidget#notifyRoot {{ background-color: {theme.SURFACE}; }}
            QLabel#durumNokta {{
                background-color: {theme.DANGER};
                margin-top: 5px;
                border-radius: 4px;
            }}
            QLabel#baslikId {{
                font-family: {theme.MONO};
                font-size: 14px;
                font-weight: 600;
            }}
            QLabel#baslikMetin {{ font-size: 14px; font-weight: 600; }}
            QLabel#altBilgi {{ font-size: 12px; color: {theme.MUTED}; }}
            QPushButton#bitirBtn {{ padding: 7px 18px; }}
        """)

        # Durum satiri: DANGER nokta + iki satirlik metin sutunu
        # ponytail: pulse animasyonu opsiyoneldi, statik nokta yeterli
        dot = QLabel()
        dot.setObjectName("durumNokta")
        dot.setFixedSize(9, 14)  # 5px ust marj + 9px nokta, basligin hizasina oturur

        title_id = QLabel(f"«{self.whoIs}»")
        title_id.setObjectName("baslikId")
        title_rest = QLabel("bilgisayarınızı yönetiyor")
        title_rest.setObjectName("baslikMetin")
        sub = QLabel("Ekranınız karşı tarafa aktarılıyor · fare kontrolü açık")
        sub.setObjectName("altBilgi")

        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        title_row.addWidget(title_id)
        title_row.addWidget(title_rest)
        title_row.addStretch()

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        text_col.addLayout(title_row)
        text_col.addWidget(sub)

        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(dot, alignment=Qt.AlignmentFlag.AlignTop)
        row.addLayout(text_col)

        exitBtn = QPushButton("Oturumu Bitir", self)
        exitBtn.setObjectName("bitirBtn")
        exitBtn.setProperty("variant", "danger")
        exitBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        exitBtn.clicked.connect(self.session_ended)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(exitBtn)

        general_layout = QVBoxLayout()
        general_layout.setContentsMargins(22, 20, 22, 20)
        general_layout.setSpacing(14)
        general_layout.addLayout(row)
        general_layout.addLayout(btn_row)
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
        try:
            self.peer.mouse_move_received.disconnect(self.moveMousePointer)
            self.peer.mouse_left_received.disconnect(self.mouseLeftClick)
            self.peer.mouse_right_received.disconnect(self.mouseRightClick)
        except (TypeError, RuntimeError):
            pass  # zaten kopmus
        # flag kapaninca yakalama dongusu biter; soket zaten kapali oldugundan
        # bloklanmis bir sendall varsa da hatayla cozulur
        self.frame_sender_worker.flag = False
        self.thread_frame_sender.quit()
        self.thread_frame_sender.wait(2000)
