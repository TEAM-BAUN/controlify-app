# Filename: main.py
import sys
import time

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from PyQt5 import QtCore

# REDIS SERVER
import redis

# UNIQUE ID OLUSTURMAK ICIN
from datetime import datetime

# REDIS SERVERINA BINARY DATA GONDEMEK ICIN
import pickle

# Goruntu Isleme Toolari
import cv2
import imutils
import mss
import numpy
import zlib


__version__ = "0.1"
__authors__ = ["Ahmet Yusuf Başaran ", "Yusufcan Günay"]

encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 25]

# * ____________________________________________
# * ______________<&>|EKRANLAR|<&>______________
# * ____________________________________________
# ? ANA EKRAN
class Controlify(QMainWindow):
    status = pyqtSignal(bool)

    def __init__(self, r, p, width, height):
        super().__init__()
        # ? Redis Instance
        # * ------------
        self.r = r
        self.p = p
        # * ------------
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
        # * ------------
        # Log to Redis server that this client is activated
        self.r.lpush("id_list", self.id)
        self.r.publish(
            "logs",
            pickle.dumps(
                {
                    "id": f"{self.id}",
                    "log_type": "client_activated",
                }
            ),
        )
        # Ana ekran Ozelliklerini tanimliyoruz
        self.setWindowTitle("Controlify")
        self.setFixedSize(QSize(750, 500))
        # Ana Ekranin Merkezine bir Widget ekliyoruz Ve Genel Bir Yerleşim alani oluşturuyoruz
        self.generalLayout = QVBoxLayout()
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)

        # Baglanti istegi gonderildiginde Ekrana Animasyon cikarilmasi
        # !Eger Redderse animasyon kapanicak ve status barda istek gonderilen kisinin ID si ile birlikte sizi <ID> reddetti mesaji gosterilecektir
        self.loading_screen = LoadingScreen()
        # PcControl Screen
        self.pc_control_screen = None

        # Ana Ekranin Icindeki Widgetlarin Olusturulmasi
        self._createHeader()
        self._createIpList()
        self._createConnTypeRadioBtns()
        self._createToBeConnectedSection()
        self._createConnectButton()
        self._createExitButton()

        self._centralWidget.setLayout(self.generalLayout)

        # ! To Activate Always Running Threads
        self.logListenerThread = LogListenerThread(self.r, self.p, self.id)
        self.logListenerThread.update_id_list_when_removed.connect(self.refreshIdList)
        self.logListenerThread.update_id_list_when_added.connect(self.refreshIdList)
        self.logListenerThread.selected_client_became_offline.connect(
            self.clearLineEditWhenServerOffline
        )
        self.logListenerThread.connection_request_handler.connect(
            self.handlePermissionResult
        )
        self.logListenerThread.show_msg_box.connect(self.showReplyBox)
        self.status.connect(self.logListenerThread.setStatus)
        self.logListenerThread.start()
        # self.logListenerThread.exit()
        # self.logListenerThread.quit()

    # todo Ana Ekrana Ait Event(Olay Kontrol Methodlari Pencere Kapatilmasi,Mouse Hareketleri vs.)
    # ? Sol ustden uygulamayi kapatirken kontrol edilen method
    def closeEvent(self, event):
        self.status.emit(True)
        reply = QMessageBox.question(
            self,
            "Message",
            "Are you sure to quit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            # Kapanirken IPyi siler
            self.r.lrem("id_list", 1, self.id)
            self.r.publish(
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

    # todo Arayuz Elemanlarini olusturan methodlar
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
        [Bağlı Bilgisayarların ip addresslerinin listesini gösteren widget]
        [Sürekli Güncel]
        """
        self.connected_ids_listwidget = QListWidget()
        self.connected_ids_listwidget.itemDoubleClicked.connect(self.setTheID)
        # self.connected_ids_listwidget.addItem("192.168.1.2")
        # self.connected_ids_listwidget.addItem("192.168.2.55")
        self.generalLayout.addWidget(self.connected_ids_listwidget)

    # def _createPcControlScreen(self):
    #     self.pc_control_screen = PcControlScreen()

    def _createConnTypeRadioBtns(self):
        horizantalBoxLayout2 = QHBoxLayout()
        self.pcControlTypeRadioBtn = QRadioButton("Bilgisayar Yönetimi")
        self.fileTransferTypeRadioBtn = QRadioButton("Dosya Transferi")
        # Varsayilan Olarak Bilgisayar Kontolu secimini belirledik!
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
        horizantalBoxLayout3.addWidget(to_be_connLabel)
        horizantalBoxLayout3.addWidget(self.to_be_connLineEdit)
        self.generalLayout.addLayout(horizantalBoxLayout3)

    def _createConnectButton(self):
        self.connBtn = QPushButton("Bağlan")
        self.connBtn.clicked.connect(self.connectToPc)
        self.generalLayout.addWidget(self.connBtn)

    def _createExitButton(self):
        self.exitBtn = QPushButton("Çıkış Yap")
        self.exitBtn.clicked.connect(self.close)
        self.generalLayout.addWidget(self.exitBtn)

    # todo Aksiyon alinan methodlar(Pc ye baglanma istegi gonderme,Guncel Ipleri alma vs.)
    def connectToPc(self):
        if not self.to_be_connLineEdit.text() == "":
            self.status.emit(True)
            self.r.publish(
                "logs",
                pickle.dumps(
                    {
                        "log_type": "connection_request",
                        "from": f"{self.id}",
                        "to": f"{self.to_be_connLineEdit.text()}",
                    }
                ),
            )
            center_position = (
                self.frameGeometry().center()
                - QtCore.QRect(QtCore.QPoint(), self.loading_screen.sizeHint()).center()
            )
            self.loading_screen.move(center_position)
            self.hide()

            self.loading_screen.startAnimation(ID=self.to_be_connLineEdit.text())

        else:
            self.statusBar().showMessage("Bir ID secmelisiniz!")
            # HATA MESAJI 3 sn sonra siliniyor
            # print("Bir ID secmelisiniz!")
            self.status.emit(False)

    def returnMainScreen(self):

        self.notify_screen = None
        self.show()

    def showReplyBox(self, id_who_wants_to_conn):
        # todo CLIENT'i mesgule al
        self.status.emit(True)

        reply = QMessageBox.question(
            self,
            "Onay",
            f"{id_who_wants_to_conn} size baglanmak istiyor onayliyormusunuz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.r.publish(
                "logs",
                pickle.dumps(
                    {
                        "log_type": "connection_request_answer",
                        "from": f"{self.id}",
                        "to": f"{id_who_wants_to_conn}",
                        "result": True,
                    }
                ),
            )
            time.sleep(0.001)
            self.hide()

            # Control Eden Bilgisayarin IDsi ile birlikle kucuk bir bilgilendirme penceresi acilir
            self.notify_screen = NotifyScreen(
                self.r, self.p, self.id, id_who_wants_to_conn
            )
            self.notify_screen.close_screen.connect(self.returnMainScreen)
            # todo  Frame gondermeye basla
        else:
            self.r.publish(
                "logs",
                pickle.dumps(
                    {
                        "log_type": "connection_request_answer",
                        "from": f"{self.id}",
                        "to": f"{id_who_wants_to_conn}",
                        "result": False,
                    }
                ),
            )
            time.sleep(0.001)
            self.status.emit(False)
            # todo client'i mesgulden cikart

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
        elif len(ids) == 0:
            self.connected_ids_listwidget.clear()

    def setTheID(self, item):
        self.to_be_connLineEdit.setText(item.text())
        # print(f"SECILEN ID : {item.text()}")

    def clearLineEditWhenServerOffline(self, id):
        if id == self.to_be_connLineEdit.text():
            self.to_be_connLineEdit.setText("")

    def handlePermissionResult(self, reply, busy):
        if reply:
            self.status.emit(True)
            # FRAME EKRANINI GOSTER
            self.hide()
            # PcKontrol Ekranini AC Frameleri al
            self.loading_screen.stopAnimation()
            self.pc_control_screen = PcControlEkrani(
                self.r, self.p, self.id, self.to_be_connLineEdit.text()
            )
            pass
        elif not reply and busy == "busy":
            self.show()
            self.loading_screen.stopAnimation()
            self.statusBar().showMessage(
                f"{self.to_be_connLineEdit.text()} IDli Client mesgul!"
            )
            self.status.emit(False)
        else:
            self.loading_screen.stopAnimation()
            self.show()
            self.statusBar().showMessage(
                f"{self.to_be_connLineEdit.text()} isteginizi reddetti"
            )
            self.status.emit(False)


# ? Looading Ekrani
class LoadingScreen(QWidget):
    def __init__(self):
        super().__init__()
        # self.setFixedSize(QSize(200, 200))
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint)
        self.movie = QMovie("spinner.gif")

        generalLayout = QVBoxLayout()

        hlbox1 = QHBoxLayout()
        hlbox2 = QHBoxLayout()
        self.connecting_to_label = QLabel(self)
        hlbox1.addWidget(self.connecting_to_label)
        self.label_animation = QLabel(self)
        self.label_animation.setMovie(self.movie)
        hlbox2.addStretch()
        hlbox2.addWidget(self.label_animation)
        hlbox2.addStretch()
        generalLayout.addLayout(hlbox1)
        generalLayout.addLayout(hlbox2)
        self.setLayout(generalLayout)

    def startAnimation(self, ID):
        self.connecting_to_label.setText(f"{ID} numaralı ID'den cevap bekleniyor")
        self.show()
        self.movie.start()

    def stopAnimation(self):
        self.movie.stop()
        self.close()


# ? Bilgisayar Kontrol Ekrani
class PcControlEkrani(QWidget):
    def __init__(self, r, p, id, i_am_controlling):
        super().__init__()
        self.r = r
        self.p = p
        self.id = id
        self.i_am_controlling = i_am_controlling
        self.setObjectName("PC Control")
        # self.setMaximumSize(1280, 720)
        self.image_frame_label = QLabel()
        self.image_frame_label.setMaximumSize(1280, 720)
        self.image_frame_label.setMouseTracking(True)

        tracker = MouseTracker(self.image_frame_label)
        tracker.positionChanged.connect(self.on_positionChanged)

        # # * Close Connection Button
        # self.close_btn = QPushButton("Bağlantıyı Sonlandır")
        # self.close_btn.clicked.connect(self.exit)
        # # * ----------------------------------- *
        self.grid = QGridLayout()
        self.grid.addWidget(self.image_frame_label)
        # self.grid.addWidget(self.close_btn)
        self.setLayout(self.grid)
        self.receiver_thread = FrameReceiverThread(
            self.r, self.p, self.id, self.i_am_controlling
        )
        self.receiver_thread.changePixmap.connect(self.setImage)
        self.receiver_thread.start()
        self.show()

    @QtCore.pyqtSlot(QtCore.QPoint)
    def on_positionChanged(self, pos):
        print((pos.x(), pos.y()))
        self.r.publish(
            "logs",
            pickle.dumps(
                {
                    "to":f"{self.i_am_controlling}",
                    "from": f"{self.id}",
                    "log_type": "mouse_position",
                    "mouse_position":f"{pos.x()}:{pos.y()}"
                }
            ),
        )

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.image_frame_label.setPixmap(QPixmap.fromImage(image))


class MouseTracker(QtCore.QObject):
    positionChanged = QtCore.pyqtSignal(QtCore.QPoint)

    def __init__(self, widget):
        super().__init__(widget)
        self._widget = widget
        self.widget.setMouseTracking(True)
        self.widget.installEventFilter(self)

    @property
    def widget(self):
        return self._widget

    def eventFilter(self, o, e):
        if o is self.widget and e.type() == QtCore.QEvent.MouseMove:
            self.positionChanged.emit(e.pos())
        return super().eventFilter(o, e)


# ? Dosya Paylasimi Ekrani
class FileTransferScreen(QWidget):
    def __init__():
        super().__init__()


# ? Kim Tarafindan Yonetildigini belirmek amacli Ekran
class NotifyScreen(QWidget):
    close_screen = pyqtSignal()

    def __init__(
        self,
        r,
        p,
        id,
        who_is_controlling,
    ):
        super().__init__()
        self.r = r
        self.p = p
        self.id = id
        self.whoIs = who_is_controlling
        # self.setFixedSize(50, 50)
        general_layout = QVBoxLayout()
        h1box = QHBoxLayout()
        h1box.addWidget(QLabel(f" {who_is_controlling}  bilgisayarinizi yonetiyor..."))
        h2box = QHBoxLayout()
        exitBtn = QPushButton("Kapat", self)
        exitBtn.clicked.connect(self.exit)
        exitBtn.setIcon(QIcon("cancel.png"))

        h2box.addStretch()
        h2box.addWidget(exitBtn)
        h2box.addStretch()
        general_layout.addLayout(h1box)
        general_layout.addLayout(h2box)
        self.setLayout(general_layout)
        self.sender_thread = FrameSenderThread(self.r, self.p, self.id, self.whoIs)
        self.sender_thread.start()
        self.show()

    def exit(self):
        self.sender_thread.flag = False
        self.close_screen.emit()


# * ______________THREADLER______________
class FrameSenderThread(QtCore.QThread):
    close_notify_screen = pyqtSignal()

    def __init__(self, r, p, id, who_is):
        super().__init__()
        self.flag = False
        # REDIS INSTANCE
        self.r = r
        self.p = p

        # My ID
        self.id = id
        # Whose ID
        self.who_is = who_is

    def run(self):
        self.flag = True
        global encode_param
        with mss.mss() as sct:
            while self.flag:
                img = numpy.array(sct.grab(sct.monitors[1]))
                result, frame = cv2.imencode(".jpg", img, encode_param)
                binary_frame = pickle.dumps(frame)
                zipped_binary_frame = zlib.compress(binary_frame)
                self.r.set("frame", zipped_binary_frame)


class FrameReceiverThread(QtCore.QThread):
    changePixmap = pyqtSignal(QImage)
    close_pc_control_screen = pyqtSignal()

    def __init__(self, r, p, id, who_is):
        super().__init__()
        self.r = r
        self.p = p
        self.id = id
        self.who_is = who_is

    def run(self):
        while True:
            zipped_binary_frame = self.r.get("frame")
            if zipped_binary_frame:
                uncompressed_binary_frame = zlib.decompress(zipped_binary_frame)
                binary_frame = pickle.loads(
                    uncompressed_binary_frame, fix_imports=True, encoding="bytes"
                )
                frame = cv2.imdecode(binary_frame, cv2.IMREAD_COLOR)
                frame = imutils.resize(frame, width=1280, height=720)
                cvt2qt = QImage(
                    frame.data,
                    frame.shape[1],
                    frame.shape[0],
                    QImage.Format_RGB888,
                )
                self.changePixmap.emit(cvt2qt)


class LogListenerThread(QThread):
    conn_req = pyqtSignal(str)
    update_id_list_when_removed = pyqtSignal(list)
    update_id_list_when_added = pyqtSignal(list)
    selected_client_became_offline = pyqtSignal(str)
    connection_request_handler = pyqtSignal(bool, str)
    show_msg_box = pyqtSignal(str)
    close_notify_screen = pyqtSignal()
    close_pc_control_screen = pyqtSignal()
    activate_main_screen = pyqtSignal(str)

    def __init__(self, r, p, id):
        super().__init__()
        # Redis Instance
        self.r = r
        self.p = p
        # Client ID gelen isteklerle karsilastirmak icin
        self.id = id
        # Connected Client ID
        self.connected_to = None
        # To Control Busy Clients
        self.status = False

    def run(self):
        # Thread surekli guncel listeyi tutuyor elinde fakat
        # sadece biri server'a katildiginda veya ayrildiginda listwidget guncellenecektir
        while True:
            time.sleep(0.001)
            updated_list = self.r.lrange("id_list", 0, -1)
            log = self.p.get_message()
            if log:
                log_dict = pickle.loads(log["data"])
                if log_dict["log_type"] == "busy":
                    if log_dict["to"] == self.id:
                        self.connection_request_handler.emit(
                            False, log_dict["log_type"]
                        )
                if log_dict["log_type"] == "client_activated":
                    # Aktif olan id yi status barda gostermek =>  Sonradan eklenilecek ozellik
                    # ip listesini guncelle
                    self.update_id_list_when_added.emit(updated_list)
                # -----------------------------------------------------------------
                if log_dict["log_type"] == "client_deactivated":
                    # ip listesini guncelle
                    self.update_id_list_when_removed.emit(updated_list)
                    # print(log_dict["data"]["id"])
                    self.selected_client_became_offline.emit(log_dict["id"])
                # -----------------------------------------------------------------
                if log_dict["log_type"] == "connection_request":
                    # Onay Message box i ac eger to kendisine esitse
                    if log_dict["to"] == self.id:
                        if self.status == False:
                            # Mesgul degilse
                            self.show_msg_box.emit(log_dict["from"])
                        else:
                            # Eger mesgulse
                            self.r.publish(
                                "logs",
                                pickle.dumps(
                                    {
                                        "log_type": "busy",
                                        "from": f"{self.id}",
                                        "to": f"{log_dict['from']}",
                                    }
                                ),
                            )
                # -----------------------------------------------------------------
                if log_dict["log_type"] == "connection_request_answer":
                    if log_dict["to"] == self.id:
                        # animasyonu durdurmak ve gelen cevaba gore fonksiyon tetiklemek
                        self.connection_request_handler.emit(log_dict["result"], "")

    def setStatus(self, status):
        self.status = status


# * ______________Redis Baglantisi______________
def redisServerSetup():
    """
    [
    ! Canli veri alisverisini saglayabilen (pubsub)
    ! ayni zamanda NoSQL gibi calisan, key:value seklinde ram hafizasinda veri saklayabilen bir database
    ]
    """
    try:
        r = redis.Redis("localhost")
        # r = redis.Redis(
        #     host="redis-11907.c135.eu-central-1-1.ec2.cloud.redislabs.com",
        #     password="jPHWcbukgy7r1qmBwa9VxNRHZmfeD9N9",
        #     port=11907,
        #     db=0,
        # )
        p = r.pubsub(ignore_subscribe_messages=True)
        p.subscribe("logs")

        # ? Requsts yani (logs)kayitlar kanalina abone olduk burda tum cihazlarin yapmak istedikleri islemlerin trafigini logluyacagiz
        # ? Buna gore clientlari uyaracagiz hali hazirda baglanti durumunda olan clientlara baglanti istegi gonderilmesini engelliyecegiz
        return (True, r, p)
    except:
        return (False, None, None)


# * ______________MAIN______________
def main():
    redisServerStatus, r, p = redisServerSetup()
    if redisServerStatus:
        controlify = QApplication(sys.argv)
        screen_resolution = controlify.desktop().screenGeometry()
        width, height = screen_resolution.width(), screen_resolution.height()
        view = Controlify(r, p, width, height)
        # ! Uygulama penceresini göstermek
        view.show()
        # ! Uygulamanin ana döngüsünü oluşturmak
        sys.exit(controlify.exec_())
    else:
        print("Redis Baglanti Sorunu Yasiyor...")


if __name__ == "__main__":
    main()


# TODOs
# 1) PcControl Ekrani