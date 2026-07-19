import logging
import time

from PySide6.QtCore import QPoint, QRect, QSize
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from Screens.Control import PcControlScreen
from Screens.Filetransfer import FileTransferScreen
from Screens.Loading import LoadingScreen
from Screens.Notify import NotifyScreen
from Utils.network import Discovery, Peer


class Main(QMainWindow):
    def __init__(self, width, height):
        super().__init__()
        self.desktop_screenX = width
        # ? Her istemci icin benzersiz (numerik) ID uretimi
        self.id = str(time.time_ns())
        # Varsayilan Baglanti Tipi
        self.connectionType = "Bilgisayar Yönetimi"

        # Ag katmani: TCP dinleyici + LAN kesfi
        self.peer = Peer(self.id)
        self.discovery = Discovery(self.id, self.peer.port)
        self.peers = {}

        # Oturum durumu
        self.awaiting_answer = False
        self.session_screen = None

        self.setupUi()
        self.connBtn.setDisabled(True)

        self.discovery.peers_changed.connect(self.refreshPeerList)
        self.peer.request_received.connect(self.manageNewConnection)
        self.peer.answer_received.connect(self.manageAnswer)
        self.peer.disconnected.connect(self.managePeerDisconnected)

        self.loading_screen = LoadingScreen()
        self.loading_screen.canceled.connect(self.requestCanceled)

    def requestCanceled(self, id_who_reject):
        # Kullanici beklemekten vazgecti; baglantiyi kapatmak karsi tarafa yeter
        self.awaiting_answer = False
        self.peer.close_connection()
        self.discovery.set_status("available")
        self.show()

    # UserInterface
    def setupUi(self):
        self.setWindowTitle("Controlify")
        self.setFixedSize(QSize(750, 500))
        self.generalLayout = QVBoxLayout()
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
        self._centralWidget.setLayout(self.generalLayout)
        # Ana Ekranin Icindeki Widgetlarin Olusturulmasi
        self._createHeader()
        self._createIpList()
        self._createConnTypeRadioBtns()
        self._createToBeConnectedSection()
        self._createConnectButton()
        self._createExitButton()

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Message",
            "Are you sure to quit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Kapanirken duyurular durur; digerleri bizi zaman asimiyla listeden dusurur
            self.discovery.stop()
            self.peer.shutdown()
            event.accept()
        else:
            event.ignore()

    def _createHeader(self):
        horizantalBoxLayout1 = QHBoxLayout()
        connected_ips_label = QLabel("Aktif Bilgisayarlarim")
        id_label = QLabel(f"ID:{self.id}")
        horizantalBoxLayout1.addWidget(connected_ips_label)
        horizantalBoxLayout1.addStretch()
        horizantalBoxLayout1.addWidget(id_label)
        self.generalLayout.addLayout(horizantalBoxLayout1)

    def _createIpList(self):
        """
        [Agdaki aktif istemcilerin ID'lerini gosteren widget]
        [UDP duyurularindan surekli guncel]
        """
        self.connected_ids_listwidget = QListWidget()
        self.connected_ids_listwidget.itemDoubleClicked.connect(self.setTheID)
        self.generalLayout.addWidget(self.connected_ids_listwidget)

    def _createConnTypeRadioBtns(self):
        horizantalBoxLayout2 = QHBoxLayout()
        self.pcControlTypeRadioBtn = QRadioButton("Bilgisayar Yönetimi")
        self.fileTransferTypeRadioBtn = QRadioButton("Dosya Transferi")
        self.pcControlTypeRadioBtn.toggled.connect(
            lambda: self.radiosBtnState(self.pcControlTypeRadioBtn)
        )
        self.fileTransferTypeRadioBtn.toggled.connect(
            lambda: self.radiosBtnState(self.fileTransferTypeRadioBtn)
        )
        self.pcControlTypeRadioBtn.setChecked(True)
        horizantalBoxLayout2.addStretch()
        horizantalBoxLayout2.addWidget(self.pcControlTypeRadioBtn)
        horizantalBoxLayout2.addWidget(self.fileTransferTypeRadioBtn)
        horizantalBoxLayout2.addStretch()
        self.generalLayout.addLayout(horizantalBoxLayout2)

    def _createToBeConnectedSection(self):
        horizantalBoxLayout3 = QHBoxLayout()
        to_be_connLabel = QLabel("Baglanilacak Bilgisayar IDsi :")
        self.to_be_connLineEdit = QLineEdit()
        self.to_be_connLineEdit.textChanged.connect(
            lambda: self.idLineEditChanged(self.to_be_connLineEdit.text())
        )
        horizantalBoxLayout3.addWidget(to_be_connLabel)
        horizantalBoxLayout3.addWidget(self.to_be_connLineEdit)
        self.generalLayout.addLayout(horizantalBoxLayout3)

    def _createConnectButton(self):
        self.connBtn = QPushButton("Bağlan")
        self.connBtn.clicked.connect(self.connectToPeer)
        self.generalLayout.addWidget(self.connBtn)

    def _createExitButton(self):
        self.exitBtn = QPushButton("Çıkış Yap")
        self.exitBtn.clicked.connect(self.close)
        self.generalLayout.addWidget(self.exitBtn)

    # Methods
    def refreshPeerList(self, peers):
        self.peers = peers
        self.connected_ids_listwidget.clear()
        for peer_id in peers:
            self.connected_ids_listwidget.addItem(peer_id)

    def manageAnswer(self, accepted, connection_type, connected_id, reason):
        if not self.awaiting_answer:
            return
        self.awaiting_answer = False
        self.loading_screen.close()
        if accepted:
            self.manageAcceptedRequest(connection_type, connected_id)
        else:
            self.peer.close_connection()
            self.discovery.set_status("available")
            self.show()
            if reason == "busy":
                QMessageBox.information(self, "Uyari!", "Kullanici mesgul!")
            else:
                QMessageBox.information(self, "Uyari!", "Kullanici sizi reddetti!")

    def manageAcceptedRequest(self, connection_type, connected_id):
        if connection_type == "Bilgisayar Yönetimi":
            screen = PcControlScreen(self.peer)
        else:
            screen = FileTransferScreen(self.peer)
        self.startSession(screen)

    def startSession(self, screen):
        self.session_screen = screen
        screen.session_ended.connect(self.endSessionByUser)
        self.hide()
        screen.show()

    def endSessionByUser(self):
        # Oturumu bu taraf kapatti; soketin kapanmasi karsi tarafi da haberdar eder
        self.peer.close_connection()
        self.teardownSession()

    def managePeerDisconnected(self):
        if self.awaiting_answer:
            # Cevap beklerken karsi taraf kapandi/koptu
            self.awaiting_answer = False
            self.loading_screen.close()
            self.discovery.set_status("available")
            self.show()
            QMessageBox.information(self, "Uyari!", "Kullaniciya ulasilamiyor!")
        elif self.session_screen is not None:
            self.teardownSession()
            QMessageBox.information(self, "Uyari!", "Baglanti sonlandirildi!")

    def teardownSession(self):
        screen, self.session_screen = self.session_screen, None
        if screen is not None:
            screen.stop()
            screen.close()
        self.discovery.set_status("available")
        self.show()

    def manageNewConnection(self, connection_type, who_wants_to_connect):
        self.discovery.set_status("busy")
        reply = QMessageBox.question(
            self,
            "Onay",
            f"{who_wants_to_connect} size baglanmak istiyor onayliyormusunuz?"
            f" Baglanma Sekli : {connection_type}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Gonderim basarisizsa istek sahibi biz cevap veremeden vazgecmis demektir
            if self.peer.send_answer(True, connection_type):
                if connection_type == "Bilgisayar Yönetimi":
                    screen = NotifyScreen(
                        self.peer, who_wants_to_connect, self.desktop_screenX
                    )
                else:
                    screen = FileTransferScreen(self.peer)
                self.startSession(screen)
            else:
                self.discovery.set_status("available")
                QMessageBox.information(
                    self, "Uyari!", "Kullanici baglanma isleminden vazgecti!"
                )
        else:
            self.peer.send_answer(False, connection_type)
            self.peer.close_connection()
            self.discovery.set_status("available")

    def radiosBtnState(self, b):
        if b.isChecked():
            self.connectionType = b.text()
            logging.info(f"Baglanti tipi:{self.connectionType}")

    def idLineEditChanged(self, text):
        if str.isnumeric(text):
            self.connBtn.setDisabled(False)
        else:
            self.connBtn.setDisabled(True)

    def setTheID(self, item):
        self.to_be_connLineEdit.setText(item.text())

    def connectToPeer(self):
        target = self.to_be_connLineEdit.text()
        info = self.peers.get(target)
        # step:1 => Hedef aktif istemciler arasinda mi?
        if info is None:
            QMessageBox.information(self, "Uyari!", "Kullanici Cevrimdisi!")
            return
        # step:2 => Hedef mesgul mu?
        if info["status"] == "busy":
            QMessageBox.information(self, "Uyari!", "Kullanici mesgul!")
            return
        # step:3 => Dogrudan TCP baglantisi kur ve istegi ilet
        self.discovery.set_status("busy")
        try:
            self.peer.connect_to(info["ip"], info["port"])
        except OSError:
            self.discovery.set_status("available")
            QMessageBox.information(self, "Uyari!", "Kullaniciya baglanilamadi!")
            return
        self.awaiting_answer = True
        self.peer.send_request(self.connectionType)
        self.hide()
        self.loading_screen.startAnimation(target)
        center_position = (
            self.frameGeometry().center()
            - QRect(QPoint(), self.loading_screen.sizeHint()).center()
        )
        self.loading_screen.move(center_position)
        logging.info(f"{target} aktif ve musait!")
