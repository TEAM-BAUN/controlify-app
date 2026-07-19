import mss
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QObject
from PySide6.QtGui import QImage, QImageWriter

# Dusuk kalite = dusuk gecikme
JPEG_QUALITY = 25


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
