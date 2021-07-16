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
        # Dosya dinleyenin benzersiz numarasi
        self.id = id
        # Dosyanin alindigi client in benzersiz numarasi
        self.who_is = who_is_sending

    def run(self):
        logging.info("Dosya Dinleniyor...")
        # Redis sunucusunun file kanalina abone olarak burdan gelecek binary verilerini dinlemeye hazirlanir
        p.subscribe("file")
        self.sayac = 0
        while True:
            file = p.get_message()
            # Gelen Binary data var mi diye surekli kontrol eder
            if file:
                # Gelen binary datasini tekrar dictionary'e donusturur
                file_dict = pickle.loads(file["data"])
                if file_dict["to"] == self.id:
                    # Eger Gelen binary data kendisine gonderilmisse bu paketi kendi hafizasina alir
                    self.sayac += 1
                    if file_dict["current_packet"] == 1:

                        self.file_name = (
                            f"indirilen-dosya-{self.sayac}{file_dict['extension']}"
                        )
                        # Python nun dosyaya yazmak icin kullandigi wb parametresiyle dosya olusturur.
                        self.f = open(
                            os.path.join(path_to_download_folder, self.file_name), "wb"
                        )
                        # Olusturulan dosyaya redisten gelen her yeni  paketi ekler
                    self.f.write(file_dict["bytes"])
                    if file_dict["current_packet"] == file_dict["packet_count"]:
                        # Eger gelen son paket ise dosyaya yazma islemini bitirir ve dosyayi kullanima hazir hale getirir.
                        self.f.close()
