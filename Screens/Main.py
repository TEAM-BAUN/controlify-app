import logging
import time

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt, QTimer
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from Screens import theme
from Screens.Confirm import ConfirmDialog
from Screens.Control import PcControlScreen
from Screens.Filetransfer import FileTransferScreen
from Screens.Loading import LoadingScreen
from Screens.Notify import NotifyScreen
from Utils.network import Discovery, Peer
from Utils.paths import asset_path


class PeerRow(QWidget):
    """Peer listesinde tek satir: durum noktasi + ID + durum metni."""

    def __init__(self, peer_id, status):
        super().__init__()
        self.setObjectName("peerRow")
        # Ayrac cizgisi (border-bottom) icin stylesheet ile boyanmali
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # Zemin seffaf; tiklama/hover listeye gecsin ki ::item stilleri calissin
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        musait = status == "available"
        renk = theme.GREEN if musait else theme.AMBER

        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background-color: {renk}; border-radius: 4px;")

        id_label = QLabel(peer_id)
        id_renk = theme.TEXT if musait else theme.BUSY_TEXT
        id_label.setStyleSheet(
            f"font-family: {theme.MONO}; font-size: 13px;"
            f" font-weight: 500; color: {id_renk};"
        )

        durum_label = QLabel("Müsait" if musait else "Meşgul")
        durum_label.setStyleSheet(f"font-size: 11px; color: {renk};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)
        layout.addWidget(dot)
        layout.addWidget(id_label)
        layout.addStretch()
        layout.addWidget(durum_label)


class Main(QMainWindow):
    def __init__(self, width, height):
        super().__init__()
        self.desktop_screenX = width
        # ? Her istemci icin benzersiz (numerik) ID uretimi
        self.id = str(time.time_ns())
        # Varsayilan Baglanti Tipi
        self.connectionType = "Bilgisayar Yönetimi"

        # Ag katmani: TCP dinleyici + LAN kesfi
        self.peer = Peer(self.id)
        self.discovery = Discovery(self.id, self.peer.port)
        self.peers = {}

        # Oturum durumu
        self.awaiting_answer = False
        self.session_screen = None

        self.setupUi()
        self.connBtn.setDisabled(True)

        self.discovery.peers_changed.connect(self.refreshPeerList)
        self.peer.request_received.connect(self.manageNewConnection)
        self.peer.answer_received.connect(self.manageAnswer)
        self.peer.disconnected.connect(self.managePeerDisconnected)

        self.loading_screen = LoadingScreen()
        self.loading_screen.canceled.connect(self.requestCanceled)

    def requestCanceled(self, id_who_reject):
        # Kullanici beklemekten vazgecti; baglantiyi kapatmak karsi tarafa yeter
        self.awaiting_answer = False
        self.peer.close_connection()
        self.discovery.set_status("available")
        self.show()

    # UserInterface
    def setupUi(self):
        self.setWindowTitle("Controlify")
        self.setFixedSize(QSize(760, 604))
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
        self.generalLayout = QVBoxLayout(self._centralWidget)
        self.generalLayout.setContentsMargins(0, 0, 0, 0)
        self.generalLayout.setSpacing(0)

        # Ana Ekranin Icindeki Widgetlarin Olusturulmasi
        self._createTopBar()
        self._createListHeader()
        self._createPeerList()
        self._createConnTypeSegmented()
        self._createTargetRow()
        self._createBottomBar()
        self._applyStyles()

    def closeEvent(self, event):
        if ConfirmDialog.ask(self, "Çıkış", "Çıkmak istediğinize emin misiniz?"):
            # Kapanirken duyurular durur; digerleri bizi zaman asimiyla listeden dusurur
            self.discovery.stop()
            self.peer.shutdown()
            event.accept()
        else:
            event.ignore()

    def _createTopBar(self):
        bar = QHBoxLayout()
        bar.setContentsMargins(22, 18, 22, 14)
        bar.setSpacing(10)

        # Logo mark'i: retina icin DPR carpani ile olceklenir
        logo = QLabel()
        logo.setFixedSize(30, 30)
        dpr = self.devicePixelRatioF()
        mark = QPixmap(asset_path("logo/mark-512.png")).scaled(
            int(30 * dpr),
            int(30 * dpr),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        mark.setDevicePixelRatio(dpr)
        logo.setPixmap(mark)

        baslik_kutusu = QVBoxLayout()
        baslik_kutusu.setSpacing(1)
        app_adi = QLabel("Controlify")
        app_adi.setObjectName("appName")
        alt_yazi = QLabel("Yerel ağ · sunucusuz")
        alt_yazi.setObjectName("appSub")
        baslik_kutusu.addWidget(app_adi)
        baslik_kutusu.addWidget(alt_yazi)

        # ID chip'i: etiket + mono ID + kopyala butonu
        chip = QFrame()
        chip.setObjectName("idChip")
        chip_layout = QHBoxLayout(chip)
        chip_layout.setContentsMargins(10, 6, 10, 6)
        chip_layout.setSpacing(8)
        chip_etiket = QLabel("Sizin ID'niz")
        chip_etiket.setObjectName("idChipLabel")
        id_degeri = QLabel(self.id)
        id_degeri.setObjectName("idValue")
        self.copyBtn = QPushButton("Kopyala")
        self.copyBtn.setObjectName("copyBtn")
        self.copyBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copyBtn.clicked.connect(self.copyIdToClipboard)
        chip_layout.addWidget(chip_etiket)
        chip_layout.addWidget(id_degeri)
        chip_layout.addWidget(self.copyBtn)

        bar.addWidget(logo)
        bar.addLayout(baslik_kutusu)
        bar.addStretch()
        bar.addWidget(chip)
        self.generalLayout.addLayout(bar)

    def _createListHeader(self):
        satir = QHBoxLayout()
        satir.setContentsMargins(22, 0, 22, 8)
        satir.setSpacing(8)

        baslik = QLabel("AKTİF BİLGİSAYARLAR")
        baslik.setObjectName("sectionTitle")
        # letter-spacing QSS'te yok; font uzerinden verilir
        font = baslik.font()
        font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 105)
        baslik.setFont(font)

        self.peerCountChip = QLabel("0")
        self.peerCountChip.setObjectName("countChip")

        satir.addWidget(baslik)
        satir.addWidget(self.peerCountChip)
        satir.addStretch()
        self.generalLayout.addLayout(satir)

    def _createPeerList(self):
        """
        [Agdaki aktif istemcilerin ID'lerini gosteren widget]
        [UDP duyurularindan surekli guncel]
        """
        panel = QFrame()
        panel.setObjectName("peerPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        self.connected_ids_listwidget = QListWidget()
        self.connected_ids_listwidget.setObjectName("peerList")
        self.connected_ids_listwidget.itemDoubleClicked.connect(self.setTheID)
        # Bos durum kaplamasini liste boyutuna esitlemek icin
        self.connected_ids_listwidget.installEventFilter(self)

        dipnot = QLabel("Çift tıklayarak hedef ID'yi seçin")
        dipnot.setObjectName("listFootnote")

        panel_layout.addWidget(self.connected_ids_listwidget)
        panel_layout.addWidget(dipnot)

        # Bos durum (2b): listeye bindirilmis kaplama
        self.emptyOverlay = QWidget(self.connected_ids_listwidget)
        self.emptyOverlay.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        kaplama = QVBoxLayout(self.emptyOverlay)
        kaplama.setSpacing(10)
        kaplama.addStretch()
        daire = QLabel("···")
        daire.setObjectName("emptyCircle")
        daire.setFixedSize(40, 40)
        daire.setAlignment(Qt.AlignmentFlag.AlignCenter)
        kaplama.addWidget(daire, 0, Qt.AlignmentFlag.AlignHCenter)
        bos_baslik = QLabel("Ağda aktif bilgisayar yok")
        bos_baslik.setObjectName("emptyTitle")
        kaplama.addWidget(bos_baslik, 0, Qt.AlignmentFlag.AlignHCenter)
        bos_aciklama = QLabel(
            "Aynı yerel ağdaki bir bilgisayarda Controlify"
            " açıldığında burada otomatik görünür."
        )
        bos_aciklama.setObjectName("emptyDesc")
        bos_aciklama.setWordWrap(True)
        bos_aciklama.setMaximumWidth(300)
        bos_aciklama.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        kaplama.addWidget(bos_aciklama, 0, Qt.AlignmentFlag.AlignHCenter)
        kaplama.addStretch()
        self.emptyOverlay.raise_()

        sarici = QHBoxLayout()
        sarici.setContentsMargins(22, 0, 22, 12)
        sarici.addWidget(panel)
        self.generalLayout.addLayout(sarici, 1)

    def _createConnTypeSegmented(self):
        satir = QHBoxLayout()
        satir.setContentsMargins(22, 0, 22, 12)
        satir.setSpacing(10)

        etiket = QLabel("Bağlantı tipi")
        etiket.setObjectName("connTypeLabel")

        pill = QFrame()
        pill.setObjectName("segPill")
        pill_layout = QHBoxLayout(pill)
        pill_layout.setContentsMargins(3, 3, 3, 3)
        pill_layout.setSpacing(3)

        self.pcControlTypeBtn = QPushButton("Bilgisayar Yönetimi")
        self.fileTransferTypeBtn = QPushButton("Dosya Transferi")
        self.connTypeGroup = QButtonGroup(self)
        self.connTypeGroup.setExclusive(True)
        for btn in (self.pcControlTypeBtn, self.fileTransferTypeBtn):
            btn.setObjectName("segBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.toggled.connect(lambda _checked, b=btn: self.radiosBtnState(b))
            self.connTypeGroup.addButton(btn)
            pill_layout.addWidget(btn)
        self.pcControlTypeBtn.setChecked(True)

        satir.addWidget(etiket)
        satir.addWidget(pill)
        satir.addStretch()
        self.generalLayout.addLayout(satir)

    def _createTargetRow(self):
        satir = QHBoxLayout()
        satir.setContentsMargins(22, 0, 22, 12)
        satir.setSpacing(10)

        self.targetBox = QFrame()
        self.targetBox.setObjectName("targetBox")
        kutu_layout = QVBoxLayout(self.targetBox)
        kutu_layout.setContentsMargins(12, 8, 12, 8)
        kutu_layout.setSpacing(0)
        ipucu = QLabel("Hedef ID")
        ipucu.setObjectName("targetHint")
        self.to_be_connLineEdit = QLineEdit()
        self.to_be_connLineEdit.setObjectName("targetInput")
        self.to_be_connLineEdit.textChanged.connect(
            lambda: self.idLineEditChanged(self.to_be_connLineEdit.text())
        )
        # Focus'ta kutu cercevesini ACCENT yapmak icin
        self.to_be_connLineEdit.installEventFilter(self)
        kutu_layout.addWidget(ipucu)
        kutu_layout.addWidget(self.to_be_connLineEdit)

        self.connBtn = QPushButton("Bağlan")
        self.connBtn.setProperty("variant", "primary")
        self.connBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.connBtn.clicked.connect(self.connectToPeer)

        satir.addWidget(self.targetBox, 1)
        satir.addWidget(self.connBtn)
        self.generalLayout.addLayout(satir)

    def _createBottomBar(self):
        bar = QHBoxLayout()
        bar.setContentsMargins(22, 10, 22, 14)
        bar.setSpacing(8)

        nokta = QLabel()
        nokta.setObjectName("onlineDot")
        nokta.setFixedSize(6, 6)
        durum = QLabel("Çevrimiçi · UDP 54545 üzerinden keşif")
        durum.setObjectName("footerText")

        self.exitBtn = QPushButton("Çıkış Yap")
        self.exitBtn.setProperty("variant", "ghost")
        self.exitBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exitBtn.clicked.connect(self.close)

        bar.addWidget(nokta)
        bar.addWidget(durum)
        bar.addStretch()
        bar.addWidget(self.exitBtn)
        self.generalLayout.addLayout(bar)

    def _applyStyles(self):
        # Ekrana ozel stiller; ortak buton varyantlari global QSS'te (theme.py)
        self.setStyleSheet(f"""
            QLabel#appName {{
                font-size: 15px;
                font-weight: 600;
                color: {theme.TEXT};
            }}
            QLabel#appSub {{ font-size: 11px; color: {theme.MUTED}; }}
            QFrame#idChip {{
                background-color: {theme.SURFACE};
                border: 1px solid {theme.BORDER};
                border-radius: 7px;
            }}
            QLabel#idChipLabel {{ font-size: 11px; color: {theme.MUTED}; }}
            QLabel#idValue {{
                font-family: {theme.MONO};
                font-size: 12px;
                font-weight: 600;
                color: {theme.TEXT};
            }}
            QPushButton#copyBtn {{
                background-color: {theme.SURFACE_2};
                color: {theme.MUTED};
                font-size: 11px;
                border: none;
                border-radius: 5px;
                padding: 3px 8px;
            }}
            QPushButton#copyBtn:hover {{ color: {theme.TEXT}; }}
            QLabel#sectionTitle {{
                font-size: 12px;
                font-weight: 600;
                color: {theme.MUTED};
            }}
            QLabel#countChip {{
                font-family: {theme.MONO};
                font-size: 11px;
                color: {theme.MUTED};
                background-color: {theme.SURFACE_2};
                border-radius: 9px;
                padding: 2px 8px;
            }}
            QFrame#peerPanel {{
                background-color: {theme.SURFACE};
                border: 1px solid {theme.BORDER};
                border-radius: 10px;
            }}
            QListWidget#peerList {{
                background-color: transparent;
                border: none;
                outline: none;
            }}
            QListWidget#peerList::item {{ padding: 0; }}
            QListWidget#peerList::item:hover {{
                background-color: {theme.ROW_HOVER};
            }}
            QListWidget#peerList::item:selected {{
                background-color: {theme.ROW_SELECTED};
            }}
            QWidget#peerRow {{
                background-color: transparent;
                border-bottom: 1px solid {theme.DIVIDER};
            }}
            QLabel#listFootnote {{
                font-size: 11px;
                color: {theme.FAINT};
                border-top: 1px solid {theme.DIVIDER};
                padding: 9px 14px;
            }}
            QLabel#emptyCircle {{
                border: 1px dashed {theme.BORDER_HOVER};
                border-radius: 20px;
                color: {theme.FAINT};
                font-size: 14px;
            }}
            QLabel#emptyTitle {{
                font-size: 13px;
                font-weight: 500;
                color: {theme.MUTED};
            }}
            QLabel#emptyDesc {{ font-size: 12px; color: {theme.FAINT}; }}
            QLabel#connTypeLabel {{
                font-size: 12px;
                font-weight: 600;
                color: {theme.MUTED};
            }}
            QFrame#segPill {{
                background-color: {theme.SURFACE};
                border: 1px solid {theme.BORDER};
                border-radius: 8px;
            }}
            QPushButton#segBtn {{
                background-color: transparent;
                color: {theme.MUTED};
                font-size: 12px;
                font-weight: 500;
                border: none;
                border-radius: 6px;
                padding: 7px 16px;
            }}
            QPushButton#segBtn:hover {{ color: {theme.TEXT}; }}
            QPushButton#segBtn:checked {{
                background-color: {theme.ACCENT};
                color: #ffffff;
                font-weight: 600;
            }}
            QFrame#targetBox {{
                background-color: {theme.SURFACE};
                border: 1px solid {theme.BORDER};
                border-radius: 8px;
            }}
            QFrame#targetBox[focused="true"] {{
                border-color: {theme.ACCENT};
            }}
            QLabel#targetHint {{ font-size: 11px; color: {theme.FAINT}; }}
            QLineEdit#targetInput {{
                background-color: transparent;
                border: none;
                font-family: {theme.MONO};
                font-size: 13px;
                color: {theme.TEXT};
                padding: 10px 0;
            }}
            QLabel#onlineDot {{
                background-color: {theme.GREEN};
                border-radius: 3px;
            }}
            QLabel#footerText {{ font-size: 11px; color: {theme.FAINT}; }}
        """)

    def eventFilter(self, watched, event):
        # Hedef kutusu focus cercevesi + bos durum kaplamasinin boyutu
        # Kurulum sirasinda liste olaylari input olusmadan gelebilir -> getattr
        if watched is getattr(self, "to_be_connLineEdit", None):
            if event.type() == QEvent.Type.FocusIn:
                self._setTargetBoxFocused(True)
            elif event.type() == QEvent.Type.FocusOut:
                self._setTargetBoxFocused(False)
        elif (
            watched is self.connected_ids_listwidget
            and event.type() == QEvent.Type.Resize
        ):
            self.emptyOverlay.setGeometry(self.connected_ids_listwidget.rect())
        return super().eventFilter(watched, event)

    def _setTargetBoxFocused(self, focused):
        self.targetBox.setProperty("focused", focused)
        self.targetBox.style().unpolish(self.targetBox)
        self.targetBox.style().polish(self.targetBox)

    def copyIdToClipboard(self):
        QApplication.clipboard().setText(self.id)
        self.copyBtn.setText("Kopyalandı")
        QTimer.singleShot(1500, lambda: self.copyBtn.setText("Kopyala"))

    # Methods
    def refreshPeerList(self, peers):
        self.peers = peers
        self.peerCountChip.setText(str(len(peers)))
        self.connected_ids_listwidget.clear()
        for peer_id, info in peers.items():
            row = PeerRow(peer_id, info["status"])
            item = QListWidgetItem()
            # setItemWidget sonrasi item.text() bos kalir; ID data'da saklanir
            item.setData(Qt.ItemDataRole.UserRole, peer_id)
            item.setSizeHint(row.sizeHint())
            self.connected_ids_listwidget.addItem(item)
            self.connected_ids_listwidget.setItemWidget(item, row)
        self.emptyOverlay.setVisible(len(peers) == 0)

    def manageAnswer(self, accepted, connection_type, connected_id, reason):
        if not self.awaiting_answer:
            return
        self.awaiting_answer = False
        self.loading_screen.close()
        if accepted:
            self.manageAcceptedRequest(connection_type, connected_id)
        else:
            self.peer.close_connection()
            self.discovery.set_status("available")
            self.show()
            if reason == "busy":
                ConfirmDialog.warn(self, "Kullanici mesgul!")
            else:
                ConfirmDialog.warn(self, "Kullanici sizi reddetti!")

    def manageAcceptedRequest(self, connection_type, connected_id):
        if connection_type == "Bilgisayar Yönetimi":
            screen = PcControlScreen(self.peer, connected_id)
        else:
            screen = FileTransferScreen(self.peer, connected_id)
        self.startSession(screen)

    def startSession(self, screen):
        self.session_screen = screen
        screen.session_ended.connect(self.endSessionByUser)
        self.hide()
        screen.show()

    def endSessionByUser(self):
        # Oturumu bu taraf kapatti; soketin kapanmasi karsi tarafi da haberdar eder
        self.peer.close_connection()
        self.teardownSession()

    def managePeerDisconnected(self):
        if self.awaiting_answer:
            # Cevap beklerken karsi taraf kapandi/koptu
            self.awaiting_answer = False
            self.loading_screen.close()
            self.discovery.set_status("available")
            self.show()
            ConfirmDialog.warn(self, "Kullaniciya ulasilamiyor!")
        elif self.session_screen is not None:
            self.teardownSession()
            ConfirmDialog.warn(self, "Baglanti sonlandirildi!")

    def teardownSession(self):
        screen, self.session_screen = self.session_screen, None
        if screen is not None:
            screen.stop()
            screen.close()
        self.discovery.set_status("available")
        self.show()

    def manageNewConnection(self, connection_type, who_wants_to_connect):
        self.discovery.set_status("busy")
        if ConfirmDialog.ask_connection(self, who_wants_to_connect, connection_type):
            # Gonderim basarisizsa istek sahibi biz cevap veremeden vazgecmis demektir
            if self.peer.send_answer(True, connection_type):
                if connection_type == "Bilgisayar Yönetimi":
                    screen = NotifyScreen(
                        self.peer, who_wants_to_connect, self.desktop_screenX
                    )
                else:
                    screen = FileTransferScreen(self.peer, who_wants_to_connect)
                self.startSession(screen)
            else:
                self.discovery.set_status("available")
                ConfirmDialog.warn(self, "Kullanici baglanma isleminden vazgecti!")
        else:
            self.peer.send_answer(False, connection_type)
            self.peer.close_connection()
            self.discovery.set_status("available")

    def radiosBtnState(self, b):
        if b.isChecked():
            self.connectionType = b.text()
            logging.info(f"Baglanti tipi:{self.connectionType}")

    def idLineEditChanged(self, text):
        if str.isnumeric(text):
            self.connBtn.setDisabled(False)
        else:
            self.connBtn.setDisabled(True)

    def setTheID(self, item):
        # ID, setItemWidget kullanildigi icin item data'sinda tutulur
        self.to_be_connLineEdit.setText(item.data(Qt.ItemDataRole.UserRole))

    def connectToPeer(self):
        target = self.to_be_connLineEdit.text()
        info = self.peers.get(target)
        # step:1 => Hedef aktif istemciler arasinda mi?
        if info is None:
            ConfirmDialog.warn(self, "Kullanici Cevrimdisi!")
            return
        # step:2 => Hedef mesgul mu?
        if info["status"] == "busy":
            ConfirmDialog.warn(self, "Kullanici mesgul!")
            return
        # step:3 => Dogrudan TCP baglantisi kur ve istegi ilet
        self.discovery.set_status("busy")
        try:
            self.peer.connect_to(info["ip"], info["port"])
        except OSError:
            self.discovery.set_status("available")
            ConfirmDialog.warn(self, "Kullaniciya baglanilamadi!")
            return
        self.awaiting_answer = True
        self.peer.send_request(self.connectionType)
        self.hide()
        self.loading_screen.startAnimation(target)
        center_position = (
            self.frameGeometry().center()
            - QRect(QPoint(), self.loading_screen.sizeHint()).center()
        )
        self.loading_screen.move(center_position)
        logging.info(f"{target} aktif ve musait!")
