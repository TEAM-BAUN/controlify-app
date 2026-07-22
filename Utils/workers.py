"""Arka plan is parcaciklari: ekran yakalama/cozme ve dosya gonderme/alma.

Frame worker'lari QThread'e moveToThread ile tasinir; FileSenderThread
dogrudan QThread alt sinifidir (tek seferlik is, run bitince biter).
"""

import logging
import os
from pathlib import Path

import mss
from PySide6.QtCore import (
    QBuffer,
    QByteArray,
    QIODevice,
    QObject,
    QThread,
    Signal,
    Slot,
)
from PySide6.QtGui import QImage, QImageWriter

# Dusuk kalite = dusuk gecikme
JPEG_QUALITY = 25
DISPLAY_WIDTH = 1280
CHUNK_SIZE = 256 * 1024
DOWNLOAD_DIR = str(Path.home() / "Downloads")


class FrameSenderWorker(QObject):
    def __init__(self, peer):
        super().__init__()
        self.peer = peer
        self.flag = False

    def run(self):
        self.flag = True
        with mss.MSS() as sct:
            while self.flag:
                shot = sct.grab(sct.monitors[1])
                # raw, QImage save bitene kadar yasamali (QImage buffer'i sahiplenmez)
                raw = shot.bgra
                image = QImage(
                    raw,
                    shot.width,
                    shot.height,
                    shot.width * 4,
                    QImage.Format.Format_ARGB32,
                )
                # QImage.save yerine QImageWriter: PySide6 stub'lariyla uyumlu tek tipli yol
                buffer = QBuffer()
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                writer = QImageWriter(buffer, QByteArray(b"jpeg"))
                writer.setQuality(JPEG_QUALITY)
                writer.write(image)
                # sendall dolu tamponda bloklar; bu da yakalama hizini
                # agin kaldirabildigi hiza dogal olarak esitler
                if not self.peer.send_frame(bytes(buffer.data().data())):
                    break  # baglanti koptu
        self.flag = False


class FrameReceiverWorker(QObject):
    """Peer'den gelen JPEG frame'leri kendi thread'inde cozup arayuze QImage iletir."""

    changePixmap = Signal(QImage)

    @Slot(bytes)
    def on_frame(self, jpeg_bytes):
        # format verilmez: JPEG, iceriğin magic byte'larindan otomatik algilanir
        image = QImage.fromData(jpeg_bytes)
        if image.isNull():
            return  # bozuk frame, atla
        self.changePixmap.emit(image.scaledToWidth(DISPLAY_WIDTH))


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
