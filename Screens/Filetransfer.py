from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QWidget,
    QProgressBar,
)

from Threads.FileListenerThread import FileListenerThread
from Threads.FileSenderThread import FileSenderThread


class FileTransferScreen(QWidget):
    def __init__(self, id, who_is):
        super().__init__()
        self.id = id
        self.who_is = who_is

        self.setupUi()
        self.startFileListenerWork()

    def setupUi(self):
        self.setWindowTitle("Dosya Paylasimi")
        self.resize(720, 480)
        self.setAcceptDrops(True)
        self.guide_label = QLabel("Göndermek istediğiniz dosyayı buraya sürükleyiniz!")
        self.pbar = QProgressBar(self)
        self.pbar.setGeometry(260, 300, 200, 25)
        self.generalLayout = QHBoxLayout()
        self.generalLayout.addStretch()
        self.generalLayout.addWidget(self.guide_label)
        self.generalLayout.addStretch()
        self.setLayout(self.generalLayout)

    def startFileListenerWork(self):
        # GUI yi dondurmamak icin Arka planda GUInin akisindan bagimsiz dosya gonderme Islemi aciyoruz
        # Parametre olarak kendi idsini ve kime gonderilecegini veriyoruz
        self.file_listener_thread = FileListenerThread(self.id, self.who_is)
        self.file_listener_thread.start()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        # Suruklenen dosyanin gerekli bilgilerini aliyoruz
        # Dosya Konumu,boyutu vs..
        file = [u.toLocalFile() for u in event.mimeData().urls()][0]
        self.file_sender_thread = FileSenderThread(file, self.id, self.who_is)
        self.file_sender_thread.finished.connect(lambda: self.setAcceptDrops(True))
        self.file_sender_thread.start()
        self.setAcceptDrops(False)
        self.guide_label.setText("Dosya Gonderiliyor")
        self.file_sender_thread.progress_level.connect(self.progress)

    def progress(self, value):
        # Progress bar i gelen dosya boyutuna gore yuzdelik olarak degistiriyoruz
        self.pbar.setValue(int(value))
        print(int(value))
        if value == 100:
            self.guide_label.setText("Dosya Gonderimi basariyla tamamlandi")
