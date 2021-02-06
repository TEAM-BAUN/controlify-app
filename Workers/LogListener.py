from PyQt5.QtCore import QObject, pyqtSignal

import pickle
import logging
import re

from Utils.redisconn import redisServerSetup

logging.basicConfig(format="%(message)s", level=logging.INFO)

status, r, p = redisServerSetup()


pattern = "^\?to=(\d+)&from=(\d+)&posX=(\d+)&posY=(\d+)"


# Step 1: Create a worker class
class LogListenerWorker(QObject):
    finished = pyqtSignal()
    update_id_list = pyqtSignal(list)
    open_new_window = pyqtSignal(str, str)
    close_notify_screen = pyqtSignal()

    reuqest_canceled = pyqtSignal()
    request_rejected = pyqtSignal()
    request_accepted = pyqtSignal(str, str)

    mouse_right_click = pyqtSignal()
    mouse_left_click = pyqtSignal()
    mouse_pointer_pos = pyqtSignal(str, str)

    def __init__(self, id):
        super().__init__()
        self.id = id
        self.flag = False

    def run(self):
        self.flag = True
        p.subscribe("logs")
        logging.info("Logs kanali dinleniyor...")
        """Long-running task."""
        # Thread surekli guncel listeyi tutuyor elinde fakat
        # sadece biri server'a katildiginda veya ayrildiginda listwidget guncellenecektir
        while self.flag:
            updated_list = r.lrange("id_list", 0, -1)
            log = p.get_message()
            if log:
                log_dict = pickle.loads(log["data"])
                if log_dict["log_type"] == "client_activated":
                    # ip listesini guncelle
                    self.update_id_list.emit(updated_list)
                # -----------------------------------------------------------------
                if log_dict["log_type"] == "client_deactivated":
                    # ip listesini guncelle
                    self.update_id_list.emit(updated_list)
                # -----------------------------------------------------------------
                if log_dict["log_type"] == "connection_request":
                    if log_dict["to"] == self.id:
                        # Onay Message box i ac eger to kendisine esitse
                        #  Connection Mode Bilgisayar yonetimi ise
                        if log_dict["connection_mode"] == "Bilgisayar Yönetimi":
                            self.open_new_window.emit(
                                "Bilgisayar Yönetimi", log_dict["from"]
                            )
                        #  Connection Mode Dosya Transferi ise
                        if log_dict["connection_mode"] == "Dosya Transferi":
                            self.open_new_window.emit(
                                "Dosya Transferi", log_dict["from"]
                            )

                # -----------------------------------------------------------------
                if log_dict["log_type"] == "connection_request_answer":
                    if log_dict["to"] == self.id:
                        if log_dict["result"] == True:
                            self.request_accepted.emit(
                                log_dict["connection_type"], log_dict["from"]
                            )
                        else:
                            self.request_rejected.emit()

                if log_dict["log_type"] == "connection_request_canceled":
                    if log_dict["to"] == self.id:
                        self.reuqest_canceled.emit()

                if log_dict["log_type"] == "control_screen_closed":
                    if log_dict["to"] == self.id:
                        self.close_notify_screen.emit()

                # if log_dict["log_type"] == "mouse_position":
                #     if log_dict["to"] == self.id:
                #         mouse_position = log_dict["mouse_position"]
                #         x_y = mouse_position.split(":")
                #         self.mouse_pointer_pos.emit(x_y[0], x_y[1])
                if log_dict["log_type"] == "mouse_left_click":
                    if log_dict["to"] == self.id:
                        self.mouse_left_click.emit()
                if log_dict["log_type"] == "mouse_right_click":
                    if log_dict["to"] == self.id:
                        self.mouse_right_click.emit()
