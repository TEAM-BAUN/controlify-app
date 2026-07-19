import logging
import os
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

DOWNLOAD_DIR = str(Path.home() / "Downloads")


class FileReceiverWorker(QObject):
    """Peer'den gelen dosya parcalarini Downloads klasorune yazar."""

    file_saved = Signal(str)  # kaydedilen dosyanin adi

    def __init__(self):
        super().__init__()
        self._file = None
        self._remaining = 0
        self._name = ""

    @Slot(str, int)
    def on_file_meta(self, name, size):
        # Guvenlik: karsi taraftan gelen isimden yol bilesenleri temizlenir
        safe_name = os.path.basename(name) or "indirilen-dosya"
        target = self._unique_path(safe_name)
        self._name = os.path.basename(target)
        self._file = open(target, "wb")
        self._remaining = size
        logging.info("Dosya aliniyor: %s (%d byte)", self._name, size)
        if size == 0:
            self._finish()

    @Slot(bytes)
    def on_file_chunk(self, data):
        if self._file is None:
            return  # meta gelmeden parca geldi, yok say
        self._file.write(data)
        self._remaining -= len(data)
        if self._remaining <= 0:
            self._finish()

    def _finish(self):
        if self._file is None:
            return
        self._file.close()
        self._file = None
        logging.info("Dosya kaydedildi: %s", self._name)
        self.file_saved.emit(self._name)

    @staticmethod
    def _unique_path(name):
        # Ayni isimde dosya varsa uzerine yazmak yerine sonuna sayi ekler
        base, ext = os.path.splitext(name)
        candidate = os.path.join(DOWNLOAD_DIR, name)
        counter = 1
        while os.path.exists(candidate):
            candidate = os.path.join(DOWNLOAD_DIR, f"{base}-{counter}{ext}")
            counter += 1
        return candidate
