from PyQt5.QtCore import QObject, pyqtSignal

import pickle
import logging
import numpy
import cv2
import zlib
import mss

from Utils.redisconn import redisServerSetup

status, r, p = redisServerSetup()

logging.basicConfig(format="%(message)s", level=logging.INFO)

# CV2 Goruntu kalitesinin yapisi
encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 25]


class FrameSenderWorker(QObject):
    close_notify_screen = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, id, who_is):
        super().__init__()
        # My ID
        self.id = id
        # Connected ID
        self.who_is = who_is
        self.flag = False

    def run(self):
        self.flag = True
        global encode_param
        with mss.mss() as sct:
            while self.flag:
                # Ekran goruntusunu alarak numpy arrayine donusturuyoruz
                img = numpy.array(sct.grab(sct.monitors[1]))
                # Goruntu sikistirmalarini gerceklestiriyoruz
                result, frame = cv2.imencode(
                    ".jpg", img, encode_param
                )  # Redis in anlayacagi bir yapi olan binary data ya ceviriyoruz
                binary_frame = pickle.dumps(frame)
                # Daha hizli islem yapabilmek icin sikistiriyoruz
                zipped_binary_frame = zlib.compress(binary_frame)
                # Redis memory database'ine sikistirilmis veriyi yaziyoruz
                r.set(f"frame:{self.id}", zipped_binary_frame)
