from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QImage

DISPLAY_WIDTH = 1280


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
