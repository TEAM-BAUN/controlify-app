import os

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from Screens import theme
from Utils.workers import FileReceiverWorker, FileSenderThread


class FileTransferScreen(QWidget):
    session_ended = Signal()

    def __init__(self, peer, target_id):
        super().__init__()
        self.peer = peer
        self.target_id = target_id
        self._stopped = False

        self.setupUi()
        self.startFileReceiver()

    def setupUi(self):
        self.setWindowTitle("Dosya Transferi")
        self.setObjectName("fileTransferScreen")
        # Ozel QWidget alt sinifinin zeminini QSS ile boyayabilmek icin sart
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.resize(640, 440)
        self.setMinimumSize(640, 440)
        self.setAcceptDrops(True)

        # --- Baslik satiri: baslik + karsi taraf chip'i ---
        title = QLabel("Dosya Transferi")
        title.setObjectName("screenTitle")

        peer_chip = QWidget()
        peer_chip.setObjectName("peerChip")
        chip_layout = QHBoxLayout(peer_chip)
        chip_layout.setContentsMargins(10, 5, 10, 5)
        chip_layout.setSpacing(7)
        peer_dot = QLabel()
        peer_dot.setObjectName("peerDot")
        peer_dot.setFixedSize(7, 7)
        peer_id = QLabel(str(self.target_id))
        peer_id.setObjectName("peerId")
        chip_layout.addWidget(peer_dot)
        chip_layout.addWidget(peer_id)

        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch()
        header.addWidget(peer_chip)

        # --- Birakma alani: kalan alani doldurur ---
        self.drop_zone = QWidget()
        self.drop_zone.setObjectName("dropZone")
        drop_layout = QVBoxLayout(self.drop_zone)
        drop_layout.setSpacing(8)
        drop_icon = QLabel("↓")
        drop_icon.setObjectName("dropIcon")
        drop_icon.setFixedSize(44, 44)
        drop_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_title = QLabel("Dosyayı buraya sürükleyin")
        drop_title.setObjectName("dropTitle")
        drop_hint = QLabel("Bırakınca gönderim otomatik başlar")
        drop_hint.setObjectName("dropHint")
        drop_layout.addStretch()
        drop_layout.addWidget(drop_icon, alignment=Qt.AlignmentFlag.AlignHCenter)
        drop_layout.addWidget(drop_title, alignment=Qt.AlignmentFlag.AlignHCenter)
        drop_layout.addWidget(drop_hint, alignment=Qt.AlignmentFlag.AlignHCenter)
        drop_layout.addStretch()

        # --- Aktarim karti: dosya adi + durum + progress (bosta gizli) ---
        self.transfer_card = QWidget()
        self.transfer_card.setObjectName("transferCard")
        card_layout = QVBoxLayout(self.transfer_card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(8)
        self.file_name_label = QLabel()
        self.file_name_label.setObjectName("fileName")
        self.status_label = QLabel()
        self.status_label.setObjectName("transferStatus")
        card_top = QHBoxLayout()
        card_top.addWidget(self.file_name_label)
        card_top.addStretch()
        card_top.addWidget(self.status_label)
        self.pbar = QProgressBar()
        self.pbar.setRange(0, 100)
        self.pbar.setTextVisible(False)
        self.pbar.setFixedHeight(5)
        card_layout.addLayout(card_top)
        card_layout.addWidget(self.pbar)
        self.transfer_card.setVisible(False)

        # --- Son transfer satiri: fileSaved gelene dek gizli ---
        self.last_row = QWidget()
        last_layout = QHBoxLayout(self.last_row)
        last_layout.setContentsMargins(0, 0, 0, 0)
        last_layout.setSpacing(6)
        last_label = QLabel("Son:")
        last_label.setObjectName("lastLabel")
        self.last_name_label = QLabel()
        self.last_name_label.setObjectName("lastName")
        last_done = QLabel("İndirildi ✓")
        last_done.setObjectName("lastDone")
        last_layout.addWidget(last_label)
        last_layout.addWidget(self.last_name_label)
        last_layout.addWidget(last_done)
        last_layout.addStretch()
        self.last_row.setVisible(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        layout.addLayout(header)
        layout.addWidget(self.drop_zone, stretch=1)
        layout.addWidget(self.transfer_card)
        layout.addWidget(self.last_row)

        # 12.5px -> 13, 11.5px -> 12 (QSS tam sayi ister, yukari yuvarlama kurali)
        self.setStyleSheet(f"""
            #fileTransferScreen {{ background-color: {theme.BG}; }}
            #screenTitle {{ font-size: 14px; font-weight: 600; color: {theme.TEXT}; }}
            #peerChip {{
                background-color: {theme.SURFACE};
                border: 1px solid {theme.BORDER};
                border-radius: 7px;
            }}
            #peerDot {{ background-color: {theme.GREEN}; border-radius: 3px; }}
            #peerId {{
                font-family: {theme.MONO};
                font-size: 12px;
                color: {theme.MUTED};
            }}
            #dropZone {{
                background-color: {theme.DROP_ZONE_BG};
                border: 2px dashed {theme.BORDER_HOVER};
                border-radius: 12px;
            }}
            #dropZone[dragover="true"] {{ border-color: {theme.ACCENT}; }}
            #dropIcon {{
                background-color: {theme.SURFACE_2};
                border-radius: 22px;
                color: {theme.ACCENT};
                font-size: 18px;
            }}
            #dropTitle {{ font-size: 13px; font-weight: 500; color: {theme.TEXT}; }}
            #dropHint {{ font-size: 12px; color: {theme.FAINT}; }}
            #transferCard {{
                background-color: {theme.SURFACE};
                border: 1px solid {theme.BORDER};
                border-radius: 10px;
            }}
            #fileName {{
                font-family: {theme.MONO};
                font-size: 13px;
                color: {theme.TEXT};
            }}
            #transferStatus {{ font-size: 11px; color: {theme.MUTED}; }}
            #transferStatus[done="true"] {{ color: {theme.GREEN}; }}
            #lastLabel {{ font-size: 11px; color: {theme.FAINT}; }}
            #lastName {{
                font-family: {theme.MONO};
                font-size: 11px;
                color: {theme.MUTED};
            }}
            #lastDone {{ font-size: 11px; color: {theme.GREEN}; }}
            QProgressBar {{
                background-color: {theme.SURFACE_2};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {theme.ACCENT};
                border-radius: 3px;
            }}
        """)

    def _setDragOver(self, on):
        # Surukleme sirasinda kesikli cerceveyi ACCENT'e cevirir
        self.drop_zone.setProperty("dragover", on)
        self.drop_zone.style().unpolish(self.drop_zone)
        self.drop_zone.style().polish(self.drop_zone)

    def _setStatus(self, text, done=False):
        self.status_label.setText(text)
        self.status_label.setProperty("done", done)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

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
        # Gelen dosya kaydedilince "Son transfer" satirini gunceller
        self.last_name_label.setText(os.path.basename(name))
        self.last_row.setVisible(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            self._setDragOver(True)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._setDragOver(False)
        event.accept()

    def dropEvent(self, event):
        # Suruklenen dosyanin yolunu alip arka planda gondermeye baslariz
        self._setDragOver(False)
        file = event.mimeData().urls()[0].toLocalFile()
        self.file_name_label.setText(os.path.basename(file))
        self.pbar.setValue(0)
        self._setStatus("Gönderiliyor · %0")
        self.transfer_card.setVisible(True)
        self.file_sender_thread = FileSenderThread(file, self.peer)
        self.file_sender_thread.finished.connect(lambda: self.setAcceptDrops(True))
        self.file_sender_thread.start()
        self.setAcceptDrops(False)
        self.file_sender_thread.progress_level.connect(self.progress)

    def progress(self, value):
        # Progress bar gonderilen veri miktarina gore yuzdelik olarak guncellenir
        self.pbar.setValue(int(value))
        if value >= 100:
            self._setStatus("Tamamlandı", done=True)
        else:
            self._setStatus(f"Gönderiliyor · %{int(value)}")

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
