from PyQt5.QtCore import QThread

import pickle
import logging
import os
from pathlib import Path

from Utils.redisconn import redisServerSetup

logging.basicConfig(format="%(message)s", level=logging.INFO)

status, r, p = redisServerSetup()

path_to_download_folder = str(os.path.join(Path.home(), "Downloads"))


class FileListenerThread(QThread):
    """Long-running task."""

    def __init__(self, id, who_is_sending):
        super().__init__()
        self.id = id
        self.who_is = who_is_sending

    def run(self):
        logging.info("Dosya Dinleniyor...")
        p.subscribe("file")
        self.sayac = 0
        while True:
            file = p.get_message()
            if file:
                file_dict = pickle.loads(file["data"])
                if file_dict["to"] == self.id:
                    self.sayac += 1
                    if file_dict["current_packet"] == 1:
                        self.file_name = (
                            f"indirilen-dosya-{self.sayac}{file_dict['extension']}"
                        )
                        self.f = open(
                            os.path.join(path_to_download_folder, self.file_name), "wb"
                        )
                    self.f.write(file_dict["bytes"])
                    if file_dict["current_packet"] == file_dict["packet_count"]:
                        self.f.close()
