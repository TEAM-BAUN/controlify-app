from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from Threads.FileListenerThread import FileReceiverWorker
from Threads.FileSenderThread import FileSenderThread


class FileTransferScreen(QWidget):
    session_ended = Signal()

    def __init__(self, peer):
        super().__init__()
        self.peer = peer
        self._stopped = False

        self.setupUi()
        self.startFileReceiver()

    def setupUi(self):
        self.setWindowTitle("Dosya Paylasimi")
        self.resize(720, 480)
        self.setAcceptDrops(True)
        self.guide_label = QLabel("Göndermek istediğiniz dosyayı buraya sürükleyiniz!")
        self.pbar = QProgressBar(self)
        layout = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(self.guide_label)
        hbox.addStretch()
        layout.addStretch()
        layout.addLayout(hbox)
        layout.addWidget(self.pbar)
        layout.addStretch()
        self.setLayout(layout)

    def startFileReceiver(self):
        # Dosya yazma islemi arayuzu dondurmamak icin ayri thread'de yapilir
        self.file_receiver_thread = QThread()
        self.file_receiver_worker = FileReceiverWorker()
        self.file_receiver_worker.moveToThread(self.file_receiver_thread)
        self.peer.file_meta_received.connect(self.file_receiver_worker.on_file_meta)
        self.peer.file_chunk_received.connect(self.file_receiver_worker.on_file_chunk)
        self.file_receiver_worker.file_saved.connect(self.fileSaved)
        self.file_receiver_thread.start()

    def fileSaved(self, name):
        self.guide_label.setText(f"Dosya indirildi: {name}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        # Suruklenen dosyanin yolunu alip arka planda gondermeye baslariz
        file = [u.toLocalFile() for u in event.mimeData().urls()][0]
        self.file_sender_thread = FileSenderThread(file, self.peer)
        self.file_sender_thread.finished.connect(lambda: self.setAcceptDrops(True))
        self.file_sender_thread.start()
        self.setAcceptDrops(False)
        self.guide_label.setText("Dosya Gonderiliyor")
        self.file_sender_thread.progress_level.connect(self.progress)

    def progress(self, value):
        # Progress bar gonderilen veri miktarina gore yuzdelik olarak guncellenir
        self.pbar.setValue(int(value))
        if value >= 100:
            self.guide_label.setText("Dosya Gonderimi basariyla tamamlandi")

    def closeEvent(self, event):
        # Pencere dogrudan kapatilirsa oturum da sonlandirilir
        if not self._stopped:
            self.session_ended.emit()
        event.accept()

    def stop(self):
        self._stopped = True
        try:
            self.peer.file_meta_received.disconnect(
                self.file_receiver_worker.on_file_meta
            )
            self.peer.file_chunk_received.disconnect(
                self.file_receiver_worker.on_file_chunk
            )
        except (TypeError, RuntimeError):
            pass  # zaten kopmus
        self.file_receiver_thread.quit()
        self.file_receiver_thread.wait(1000)
