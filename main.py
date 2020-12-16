# Filename: main.py
import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


import redis
from redis import exceptions

__version__ = "0.1"
__authors__ = ["Ahmet Yusuf Başaran ", "Yusufcan Günay"]


# * ______________EKRANLAR______________

# ? ANA EKRAN
class Controlify(QMainWindow):
    def __init__(self, r, p):
        super().__init__()
        # Ana ekran Ozelliklerini tanimliyoruz
        self.setWindowTitle("Controlify")
        self.setFixedSize(QSize(750, 500))
        # Ana Ekranin Merkezine bir Widget ekliyoruz Ve Genel Bir Yerleşim alani oluşturuyoruz
        self.generalLayout = QVBoxLayout()
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)

        # Ana Ekranin Icindeki Widgetlarin Olusturulmasi
        self._createHeader()
        self._createIpList()
        self._createConnTypeRadioBtns()
        self._createConnectButton()

        self._centralWidget.setLayout(self.generalLayout)

    # todo Arayuz Elemanlarini olusturan methodlar
    def _createHeader(self):
        self.connected_ips_label = QLabel("Aktif Bilgisayarlarim")
        self.generalLayout.addWidget(self.connected_ips_label)

    def _createIpList(self):
        """
        [Bağlı Bilgisayarların ip addresslerinin listesini gösteren widget]
        [Sürekli Güncel]
        """
        self.connected_ips_listwidget = QListWidget()
        self.connected_ips_listwidget.addItem("192.168.1.2")
        self.connected_ips_listwidget.addItem("192.168.2.55")
        self.generalLayout.addWidget(self.connected_ips_listwidget)

    def _createPcControlScreen(self):
        self.pc_control_screen = PcControlScreen()

    def _createConnTypeRadioBtns(self):
        horizantalBoxLayout = QHBoxLayout()
        self.pcControlTypeRadioBtn = QRadioButton("Bilgisayar Yönetimi")
        self.fileTransferTypeRadioBtn = QRadioButton("Dosya Transferi")
        # Varsayilan Olarak Bilgisayar Kontolu secimini belirledik!
        self.pcControlTypeRadioBtn.setChecked(True)
        horizantalBoxLayout.addWidget(self.pcControlTypeRadioBtn)
        horizantalBoxLayout.addWidget(self.fileTransferTypeRadioBtn)
        self.generalLayout.addLayout(horizantalBoxLayout)

    def _createConnectButton(self):
        self.connBtn = QPushButton("Bağlan")
        self.connBtn.clicked.connect(self.connectToPc)
        self.generalLayout.addWidget(self.connBtn)

    # todo Aksiyon alinan methodlar(Pc ye baglanma istegi gonderme,Guncel Ipleri alma vs.)
    def connectToPc(self):
        pass


# ? Bilgisayar Kontrol Ekrani
class PcControlScreen(QWidget):
    def __init__():
        super().__init__()


# ? Dosya Paylasimi Ekrani
class FileTransferScreen(QWidget):
    def __init__():
        super().__init__()


# * ______________THREADLER______________

# * ______________MAIN______________
def main():
    redisServerStatus, r, p = redisServerSetup()
    if redisServerStatus:
        try:
            controlify = QApplication(sys.argv)
            view = Controlify(r, p)
            # ! Uygulama penceresini göstermek
            view.show()
            # ! Uygulamanin ana döngüsünü oluşturmak
            sys.exit(controlify.exec_())
        except:
            print("PyQt uygulamasinin baslatilmasinda sorun yasandi!")
    else:
        print("Redis Baglanti Sorunu Yasiyor...")


# * ______________Redis Baglantisi______________
def redisServerSetup():
    """
    [
    ! Canli veri alisverisini saglayabilen
    ! ayni zamanda NoSQL gibi calisan, key:value seklinde ram hafizasinda veri saklayabilen bir database
    ]
    """
    try:
        r = redis.Redis(
            host="redis-11907.c135.eu-central-1-1.ec2.cloud.redislabs.com",
            password="jPHWcbukgy7r1qmBwa9VxNRHZmfeD9N9",
            port=11907,
            db=0,
        )
        p = r.pubsub(ignore_subscribe_messages=True)
        # ? Requsts yani istekler kanalina abone olduk burda tum cihazlarin yapmak istedikleri islemlerin trafigini logluyacagiz
        # ? Buna gore clientlari uyaracagiz hali hazirda baglanti durumunda olan clientlara baglanti istegi gonderilmesini engelliyecegiz
        p.subscribe("requests")
        return (True, r, p)
    except:
        return (False, None, None)


if __name__ == "__main__":
    main()