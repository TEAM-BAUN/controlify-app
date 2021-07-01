from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QImage

import pickle
import logging
import imutils
import cv2
import zlib

from Utils.redisconn import redisServerSetup

logging.basicConfig(format="%(message)s", level=logging.INFO)

status, r, p = redisServerSetup()


class FrameReceiverWorker(QObject):
    changePixmap = pyqtSignal(QImage)
    close_pc_control_screen = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, id, who_is):
        super().__init__()
        self.id = id
        self.who_is = who_is
        self.flag = False

    def run(self):
        self.flag = True
        while self.flag:
            # Redis Memory database'den guncel frame'i cekiyoruz
            zipped_binary_frame = r.get(f"frame:{self.who_is}")
            if zipped_binary_frame:
                # Zipli halde gelen frame i aciyoruz
                uncompressed_binary_frame = zlib.decompress(zipped_binary_frame)
                # Binary olarak gelen zipden cikmis veriyi tekrar python nun anliyacagi yapiya donusturuyoruz
                binary_frame = pickle.loads(
                    uncompressed_binary_frame, fix_imports=True, encoding="bytes"
                )
                # Goruntu islemelerini gerceklestiriyoruz
                frame = cv2.imdecode(binary_frame, cv2.IMREAD_COLOR)
                frame = imutils.resize(frame, width=1280, height=720)
                cvt2qt = QImage(
                    frame.data,
                    frame.shape[1],
                    frame.shape[0],
                    QImage.Format_BGR888,
                )
                self.changePixmap.emit(cvt2qt)
