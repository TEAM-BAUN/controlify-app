from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# Ekranlar
from Screens.Control import PcControlScreen
from Screens.Notify import NotifyScreen
from Screens.Loading import LoadingScreen
from Screens.Filetransfer import FileTransferScreen


from datetime import datetime
import logging
import pickle
import time


logging.basicConfig(format="%(message)s", level=logging.INFO)

from Workers.LogListener import LogListenerWorker

from Utils.redisconn import redisServerSetup

status, r, p = redisServerSetup()


class Main(QMainWindow):
    def __init__(self, width, height):
        super().__init__()
        # ? Desktop Screen Size
        # * ------------
        self.desktop_screenX = width
        self.desktop_screenY = height
        # * ------------
        # ? Unique ID creation for every client
        # * ------------
        now = datetime.now()
        id = str.join("", str(datetime.timestamp(now)).split("."))
        self.id = id
        # Varsayilan Baglanti Tipi
        self.connectionType = "Bilgisayar Yönetimi"
        # * ------------
        self.setupUi()
        self.connBtn.setDisabled(True)
        self.startLogListenerWorker()
        r.lpush("id_list", self.id)
        r.publish(
            "logs",
            pickle.dumps(
                {
                    "id": f"{self.id}",
                    "log_type": "client_activated",
                }
            ),
        )
        r.set(f"status:{self.id}", "available", ex=3600)
        self.loading_screen = LoadingScreen()
        self.loading_screen.show_main.connect(self.show)
        self.loading_screen.now_available.connect(
            lambda: r.set(f"status:{self.id}", "available", ex=3600)
        )
        self.loading_screen.request_cancaled.connect(self.requestCanceled)
        self.isRequestCanceled = None

    def requestCanceled(self, id_who_reject):
        r.publish(
            "logs",
            pickle.dumps(
                {
                    "log_type": "connection_request_canceled",
                    "from": f"{self.id}",
                    "to": f"{id_who_reject}",
                }
            ),
        )

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
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            # Kapanirken IPyi siler
            r.lrem("id_list", 1, self.id)
            r.publish(
                "logs",
                pickle.dumps(
                    {
                        "id": f"{self.id}",
                        "log_type": "client_deactivated",
                    }
                ),
            )
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
        [Bağlı Bilgisayarların ID'lerini gösteren widget]
        [Sürekli Güncel]
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
        self.connBtn.clicked.connect(self.connect)
        self.generalLayout.addWidget(self.connBtn)

    def _createExitButton(self):
        self.exitBtn = QPushButton("Çıkış Yap")
        self.exitBtn.clicked.connect(self.close)
        self.generalLayout.addWidget(self.exitBtn)

    # Methods
    def startLogListenerWorker(self):
        # Step 2: Create a QThread object
        self.log_listener_thread = QThread()
        self.log_listener_thread.isRunning()
        # Step 3: Create a worker object
        self.logListenerWorker = LogListenerWorker(self.id)
        self.logListenerWorker.moveToThread(self.log_listener_thread)
        self.logListenerWorker.update_id_list.connect(self.refreshIdList)
        self.logListenerWorker.finished.connect(self.log_listener_thread.quit)
        self.logListenerWorker.finished.connect(self.logListenerWorker.deleteLater)
        self.log_listener_thread.finished.connect(self.log_listener_thread.deleteLater)
        self.log_listener_thread.started.connect(self.logListenerWorker.run)
        self.logListenerWorker.open_new_window.connect(self.manageNewConnection)
        self.logListenerWorker.request_rejected.connect(self.manageRejectedRequest)
        self.logListenerWorker.request_accepted.connect(self.manageAcceptedRequest)
        # Step 4: Move worker to the thread
        self.log_listener_thread.start()

    def manageAcceptedRequest(self, connection_type, connected_id):
        self.loading_screen.close()
        if connection_type == "Bilgisayar Yönetimi":
            self.control = PcControlScreen(self.id, connected_id)
            self.control.close_control_screen.connect(self.closeControlScreen)
            self.control.show()
        else:
            self.logListenerWorker.flag = False
            self.log_listener_thread.quit()
            self.logListenerWorker.deleteLater()
            self.log_listener_thread.deleteLater()
            self.file_transfer_screen = FileTransferScreen(self.id, connected_id)
            self.file_transfer_screen.show()
            self.close()
            

    def closeControlScreen(self, who_closed):
        self.control.frame_receiver_worker.flag = False
        self.control.frame_receiver_thread.quit()
        self.control.frame_receiver_worker.deleteLater()
        self.control.frame_receiver_thread.deleteLater()
        self.control.close()
        self.show()
        r.publish(
            "logs",
            pickle.dumps(
                {
                    "log_type": "control_screen_closed",
                    "from": f"{self.id}",
                    "to": f"{who_closed}",
                }
            ),
        )
        r.set(f"status:{self.id}", "available")

    def closeNotifyScreen(self):
        self.notify_screen.thread_frame_sender.quit()
        self.notify_screen.frame_sender_worker.deleteLater()
        self.notify_screen.thread_frame_sender.deleteLater()
        self.notify_screen.close()
        r.set(f"status:{self.id}", "available")
        self.show()

    def manageRejectedRequest(self):
        self.loading_screen.close()
        self.show()
        QMessageBox.information(self, "Uyari!", "Kullanici sizi reddetti!")

    def manageNewConnection(self, connection_type, who_wants_to_connect):
        r.set(f"status:{self.id}", "busy")
        reply = QMessageBox.question(
            self,
            "Onay",
            f"{who_wants_to_connect} size baglanmak istiyor onayliyormusunuz? Baglanma Sekli : {connection_type}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if self.isRequestCanceled is None:
            if reply == QMessageBox.Yes:
                r.publish(
                    "logs",
                    pickle.dumps(
                        {
                            "log_type": "connection_request_answer",
                            "from": f"{self.id}",
                            "to": f"{who_wants_to_connect}",
                            "result": True,
                            "connection_type": f"{connection_type}",
                        }
                    ),
                )
                time.sleep(0.002)
                logging.info(connection_type)
                # todo 1 Baglanti tipine ait olan ekran acilacaktir!
                if connection_type == "Bilgisayar Yönetimi":
                    # todo 2 Bilgisayar Yonetimi Ekranini acmak
                    self.notify_screen = NotifyScreen(
                        self.id, who_wants_to_connect, self.desktop_screenX
                    )
                    self.notify_screen.backtoMain.connect(self.notifyScreenClosed)
                    self.logListenerWorker.close_notify_screen.connect(
                        self.closeNotifyScreen
                    )
                    self.logListenerWorker.mouse_left_click.connect(
                        self.notify_screen.mouseLeftClick
                    )
                    self.logListenerWorker.mouse_right_click.connect(
                        self.notify_screen.mouseRightClick
                    )
                    self.logListenerWorker.mouse_pointer_pos.connect(
                        self.notify_screen.moveMousePointer
                    )
                    self.hide()
                    self.notify_screen.show()
                else:
                    # todo 2 Dosya Transferi ekranini Ekranini acmak
                    self.file_transfer_screen = FileTransferScreen(
                        self.id, who_wants_to_connect
                    )
                    self.hide()
                    self.file_transfer_screen.show()
            else:
                r.publish(
                    "logs",
                    pickle.dumps(
                        {
                            "log_type": "connection_request_answer",
                            "from": f"{self.id}",
                            "to": f"{who_wants_to_connect}",
                            "result": False,
                        }
                    ),
                )
                time.sleep(0.001)
                r.set(f"status:{self.id}", "available")
        else:
            logging.info("Kullanici baglanma isleminden vazgecti!")
            QMessageBox.information(
                self, "Uyari!", "Kullanici baglanma isleminden vazgecti!"
            )
            r.set(f"status:{self.id}", "available")

    def notifyScreenClosed(self):
        self.notify_screen.close()
        self.show()
        r.set(f"status:{self.id}", "available")

    def refreshIdList(self, ids):
        if len(ids) > 0:
            decoded_ids = [x.decode("utf-8") for x in ids]
            # Kendi idsini siliyoruz
            # print(decoded_ids)
            # Client'in kendi ipsini siliyoruz ;)
            for id in decoded_ids:
                if id == self.id:
                    decoded_ids.remove(id)
            # print(decoded_ids)
            # Listemizi guncel listeyle degistirmek icin siliyoruz
            self.connected_ids_listwidget.clear()
            # Yeni idleri listeye ekliyoruz
            if len(decoded_ids) > 0:
                for id in decoded_ids:
                    self.connected_ids_listwidget.addItem(id)
        # elif len(ids) == 0:
        #     self.connected_ids_listwidget.clear()

    def radiosBtnState(self, b):
        if b.text() == "Bilgisayar Yönetimi":
            if b.isChecked() == True:
                self.connectionType = "Bilgisayar Yönetimi"
                logging.info(f"Baglanti tipi:{self.connectionType}")
            else:
                pass

        if b.text() == "Dosya Transferi":
            if b.isChecked() == True:
                self.connectionType = "Dosya Transferi"
                logging.info(f"Baglanti tipi:{self.connectionType}")
            else:
                pass

    def idLineEditChanged(self, text):
        # logging.info(text)
        if str.isnumeric(text):
            self.connBtn.setDisabled(False)
        else:
            self.connBtn.setDisabled(True)

    def setTheID(self, item):
        self.to_be_connLineEdit.setText(item.text())

    def connect(self):
        # step:0 => Bu client i mesgul durumuna getir!
        # 1 gun sonra key silinecek
        r.set(f"status:{self.id}", "busy", ex=3600)
        # step:1 => En guncel listeyi cekmek
        updated_list = r.lrange("id_list", 0, -1)
        ids = [x.decode("utf-8") for x in updated_list]
        # Client'in kendi idsini siliyoruz
        for id in ids:
            if id == self.id:
                ids.remove(id)
        # step:2 => Baglanilacak ID aktif bilgisayarlar arasinda olup olmadigini kontrol et!

        # logging.info(f"{ids}")

        exist = self.to_be_connLineEdit.text() in ids
        if exist:
            if (
                r.get(f"status:{self.to_be_connLineEdit.text()}").decode("utf-8")
                == "busy"
            ):
                # logging.info(f"{self.to_be_connLineEdit.text()} aktif ama mesgul!")
                r.set(f"status:{self.id}", "available", ex=3600)
                reply = QMessageBox.information(self, "Uyari!", "Kullanici mesgul!")
            else:
                self.hide()
                self.loading_screen.startAnimation(self.to_be_connLineEdit.text())
                center_position = (
                    self.frameGeometry().center()
                    - QRect(QPoint(), self.loading_screen.sizeHint()).center()
                )
                self.loading_screen.move(center_position)
                logging.info(f"{self.to_be_connLineEdit.text()} aktif ve musait!")
                r.publish(
                    "logs",
                    pickle.dumps(
                        {
                            "connection_mode": f"{self.connectionType}",
                            "log_type": "connection_request",
                            "from": f"{self.id}",
                            "to": f"{self.to_be_connLineEdit.text()}",
                        }
                    ),
                )
        else:
            r.set(f"status:{self.id}", "available", ex=3600)
            QMessageBox.information(self, "Uyari!", "Kullanici Cevrimdisi!")
            # logging.info(f"{self.to_be_connLineEdit.text()} cevrimdisi!")
        # step:3 => Eger aktif bilgisayarlar arasindaysa log kanalina baglanti istegini ilet
