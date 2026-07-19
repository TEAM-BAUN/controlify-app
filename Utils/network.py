"""P2P ag katmani.

Redis'in yerini alan iki parca:
- Discovery: UDP broadcast ile LAN'daki istemcileri bulur ve kendini duyurur.
- Peer: Iki istemci arasindaki tek TCP baglantisini yonetir; gelen mesajlari
  Qt sinyallerine cevirir.

Mesaj cercevesi: 4 byte payload uzunlugu (big-endian) + 1 byte mesaj tipi + payload.
Kontrol mesajlari JSON, frame ve dosya parcalari ham binary tasinir.
Agdan gelen veri asla pickle ile acilmaz.
"""

import json
import logging
import socket
import struct
import threading
import time

from PySide6.QtCore import QObject, Signal

DISCOVERY_PORT = 54545
ANNOUNCE_INTERVAL = 1.0  # saniye
PEER_TIMEOUT = 3.0  # bu sure duyuru gelmezse istemci listeden duser

_HEADER = struct.Struct(">IB")
_MOUSE = struct.Struct(">II")

# Mesaj tipleri
MSG_REQUEST = 1
MSG_ANSWER = 2
MSG_FRAME = 10
MSG_MOUSE_MOVE = 20
MSG_MOUSE_LEFT = 21
MSG_MOUSE_RIGHT = 22
MSG_FILE_META = 30
MSG_FILE_CHUNK = 31

# Bozuk/kotu niyetli basliklarin devasa alloc yapmasini engeller
MAX_PAYLOAD = 32 * 1024 * 1024


def pack_message(msg_type, payload=b""):
    return _HEADER.pack(len(payload), msg_type) + payload


def recv_exact(sock, size):
    """Soketten tam olarak `size` byte okur; baglanti koparsa ConnectionError."""
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("baglanti kapandi")
        data.extend(chunk)
    return bytes(data)


def read_message(sock):
    length, msg_type = _HEADER.unpack(recv_exact(sock, _HEADER.size))
    if length > MAX_PAYLOAD:
        raise ConnectionError("gecersiz mesaj boyutu")
    return msg_type, recv_exact(sock, length)


class Discovery(QObject):
    """UDP broadcast ile LAN kesfi.

    Her istemci periyodik olarak {id, port, status} duyurur; dinleyen taraf
    duyurunun geldigi IP'yi kaynak adresten ogrenir. PEER_TIMEOUT icinde
    duyuru yenilenmezse istemci listeden dusurulur.
    """

    # {id: {"ip": str, "port": int, "status": str}}
    peers_changed = Signal(dict)

    def __init__(self, my_id, tcp_port):
        super().__init__()
        self.my_id = my_id
        self.tcp_port = tcp_port
        self.status = "available"
        self._peers = {}  # id -> (ip, port, status, last_seen)
        self._last_emitted = {}
        self._running = True
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Ayni makinede birden fazla istemci calisabilsin (test/demo)
        if hasattr(socket, "SO_REUSEPORT"):
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._sock.bind(("", DISCOVERY_PORT))
        self._sock.settimeout(0.5)
        threading.Thread(target=self._announce_loop, daemon=True).start()
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def set_status(self, status):
        self.status = status
        self._announce()  # yeni durumu beklemeden hemen duyur

    def stop(self):
        self._running = False
        self._sock.close()

    def _announce(self):
        payload = json.dumps(
            {"id": self.my_id, "port": self.tcp_port, "status": self.status}
        ).encode()
        try:
            self._sock.sendto(payload, ("255.255.255.255", DISCOVERY_PORT))
        except OSError:
            pass

    def _announce_loop(self):
        while self._running:
            self._announce()
            time.sleep(ANNOUNCE_INTERVAL)

    def _listen_loop(self):
        while self._running:
            try:
                data, addr = self._sock.recvfrom(4096)
            except socket.timeout:
                pass
            except OSError:
                break
            else:
                try:
                    info = json.loads(data)
                    peer_id = str(info["id"])
                    if peer_id != self.my_id:
                        self._peers[peer_id] = (
                            addr[0],
                            int(info["port"]),
                            str(info["status"]),
                            time.monotonic(),
                        )
                except (ValueError, KeyError, TypeError):
                    continue  # bozuk duyuru, yok say
            self._prune_and_emit()

    def _prune_and_emit(self):
        now = time.monotonic()
        self._peers = {
            pid: entry
            for pid, entry in self._peers.items()
            if now - entry[3] < PEER_TIMEOUT
        }
        snapshot = {
            pid: {"ip": ip, "port": port, "status": status}
            for pid, (ip, port, status, _) in self._peers.items()
        }
        if snapshot != self._last_emitted:
            self._last_emitted = snapshot
            self.peers_changed.emit(snapshot)


class Peer(QObject):
    """Tek bir karsi ucla TCP baglantisi.

    Uygulama acilir acilmaz dinlemeye baslar (port isletim sisteminden alinir,
    Discovery uzerinden duyurulur). Ayni anda tek oturum desteklenir; mesgulken
    gelen baglantilar otomatik reddedilir.
    """

    request_received = Signal(str, str)  # mode, peer_id
    answer_received = Signal(bool, str, str, str)  # accepted, mode, peer_id, reason
    disconnected = Signal()
    frame_received = Signal(bytes)
    mouse_move_received = Signal(int, int)
    mouse_left_received = Signal()
    mouse_right_received = Signal()
    file_meta_received = Signal(str, int)  # name, size
    file_chunk_received = Signal(bytes)

    def __init__(self, my_id):
        super().__init__()
        self.my_id = my_id
        self._conn = None
        self._send_lock = threading.Lock()
        self._expected_close = False
        self._running = True
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(("", 0))
        self._server.listen(1)
        self.port = self._server.getsockname()[1]
        threading.Thread(target=self._accept_loop, daemon=True).start()

    # ---- baglanti yonetimi ----

    def connect_to(self, ip, port):
        """Karsi tarafa baglanir. Basarisiz olursa OSError firlatir."""
        if self._conn is not None:
            raise OSError("zaten aktif bir baglanti var")
        conn = socket.create_connection((ip, port), timeout=3)
        conn.settimeout(None)
        self._attach(conn)

    def close_connection(self):
        """Aktif baglantiyi bilerek kapatir; karsi taraf disconnected sinyali alir.

        (QObject.disconnect'i golgelememek icin bu isim secildi.)
        """
        self._expected_close = True
        self._close_conn()

    def shutdown(self):
        self._running = False
        self._expected_close = True
        self._server.close()
        self._close_conn()

    @property
    def connected(self):
        return self._conn is not None

    def _attach(self, conn):
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._expected_close = False
        self._conn = conn
        threading.Thread(target=self._reader, args=(conn,), daemon=True).start()

    def _accept_loop(self):
        while self._running:
            try:
                conn, _ = self._server.accept()
            except OSError:
                break
            # ponytail: tekli oturum; ayni anda ikinci baglanti aninda "busy" ile reddedilir
            if self._conn is not None:
                try:
                    reject = json.dumps(
                        {
                            "id": self.my_id,
                            "accepted": False,
                            "mode": "",
                            "reason": "busy",
                        }
                    ).encode()
                    conn.sendall(pack_message(MSG_ANSWER, reject))
                    conn.close()
                except OSError:
                    pass
                continue
            self._attach(conn)

    def _close_conn(self):
        conn, self._conn = self._conn, None
        if conn is not None:
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            conn.close()

    def _reader(self, conn):
        try:
            while True:
                msg_type, payload = read_message(conn)
                self._dispatch(msg_type, payload)
        except (ConnectionError, OSError):
            pass
        finally:
            expected = self._expected_close
            if self._conn is conn:
                self._close_conn()
            if not expected:
                self.disconnected.emit()

    def _dispatch(self, msg_type, payload):
        try:
            if msg_type == MSG_REQUEST:
                info = json.loads(payload)
                self.request_received.emit(str(info["mode"]), str(info["id"]))
            elif msg_type == MSG_ANSWER:
                info = json.loads(payload)
                self.answer_received.emit(
                    bool(info["accepted"]),
                    str(info.get("mode", "")),
                    str(info.get("id", "")),
                    str(info.get("reason", "")),
                )
            elif msg_type == MSG_FRAME:
                self.frame_received.emit(payload)
            elif msg_type == MSG_MOUSE_MOVE:
                x, y = _MOUSE.unpack(payload)
                self.mouse_move_received.emit(x, y)
            elif msg_type == MSG_MOUSE_LEFT:
                self.mouse_left_received.emit()
            elif msg_type == MSG_MOUSE_RIGHT:
                self.mouse_right_received.emit()
            elif msg_type == MSG_FILE_META:
                info = json.loads(payload)
                self.file_meta_received.emit(str(info["name"]), int(info["size"]))
            elif msg_type == MSG_FILE_CHUNK:
                self.file_chunk_received.emit(payload)
        except (ValueError, KeyError, TypeError, struct.error):
            logging.warning("Bozuk mesaj yok sayildi (tip=%s)", msg_type)

    # ---- gonderim ----

    def _send(self, msg_type, payload=b""):
        conn = self._conn
        if conn is None:
            return False
        try:
            with self._send_lock:
                conn.sendall(pack_message(msg_type, payload))
            return True
        except OSError:
            self._close_conn()
            return False

    def send_request(self, mode):
        return self._send(
            MSG_REQUEST, json.dumps({"id": self.my_id, "mode": mode}).encode()
        )

    def send_answer(self, accepted, mode, reason=""):
        return self._send(
            MSG_ANSWER,
            json.dumps(
                {"id": self.my_id, "accepted": accepted, "mode": mode, "reason": reason}
            ).encode(),
        )

    def send_frame(self, jpeg_bytes):
        return self._send(MSG_FRAME, jpeg_bytes)

    def send_mouse_move(self, x, y):
        return self._send(MSG_MOUSE_MOVE, _MOUSE.pack(max(0, int(x)), max(0, int(y))))

    def send_mouse_left(self):
        return self._send(MSG_MOUSE_LEFT)

    def send_mouse_right(self):
        return self._send(MSG_MOUSE_RIGHT)

    def send_file_meta(self, name, size):
        return self._send(
            MSG_FILE_META, json.dumps({"name": name, "size": size}).encode()
        )

    def send_file_chunk(self, data):
        return self._send(MSG_FILE_CHUNK, data)
