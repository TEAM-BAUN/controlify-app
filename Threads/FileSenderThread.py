import logging
import os

from PySide6.QtCore import QThread, Signal

CHUNK_SIZE = 256 * 1024


class FileSenderThread(QThread):
    progress_level = Signal(float)

    def __init__(self, path, peer):
        super().__init__()
        self.file_path = path
        self.peer = peer

    def run(self):
        logging.info("Dosya gonderiliyor...")
        size = os.path.getsize(self.file_path)
        name = os.path.basename(self.file_path)
        if not self.peer.send_file_meta(name, size):
            return
        sent = 0
        with open(self.file_path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                if not self.peer.send_file_chunk(chunk):
                    return  # baglanti koptu
                sent += len(chunk)
                self.progress_level.emit(sent * 100 / size)
        if size == 0:
            self.progress_level.emit(100)
        logging.info("Dosya gonderme islemi tamamlandi!")
