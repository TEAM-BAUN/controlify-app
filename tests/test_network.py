"""Ag katmaninin loopback uzerinde calisan kendi kendine testi.

Calistirma: uv run python tests/test_network.py
Framework yok; her adim assert ile dogrulanir, hata aninda satir belli olur.
"""

import os
import socket
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QCoreApplication

from Utils.network import (
    MSG_FRAME,
    Discovery,
    Peer,
    pack_message,
    read_message,
)


def wait_for(cond, timeout=5.0):
    # Sinyaller reader thread'lerinden ana thread'e kuyruklanir;
    # gercek uygulamada app.exec() yapan teslimati burada processEvents yapar
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        QCoreApplication.processEvents()
        if cond():
            return True
        time.sleep(0.01)
    return False


def test_framing():
    a, b = socket.socketpair()
    payload = b"\x00\x01binary\xff" * 100
    a.sendall(pack_message(MSG_FRAME, payload))
    msg_type, received = read_message(b)
    assert msg_type == MSG_FRAME
    assert received == payload
    a.close()
    b.close()
    print("PASS framing")


def test_peer_session():
    a = Peer("1111")
    b = Peer("2222")
    got = {
        "requests": [],
        "answers": [],
        "frames": [],
        "mouse": [],
        "clicks": [],
        "files": [],
        "chunks": [],
        "a_disconnected": 0,
        "b_disconnected": 0,
    }
    a.request_received.connect(lambda mode, pid: got["requests"].append((mode, pid)))
    b.answer_received.connect(
        lambda ok, mode, pid, why: got["answers"].append((ok, mode, pid, why))
    )
    b.frame_received.connect(lambda data: got["frames"].append(data))
    a.mouse_move_received.connect(lambda x, y: got["mouse"].append((x, y)))
    a.mouse_left_received.connect(lambda: got["clicks"].append("left"))
    a.file_meta_received.connect(lambda n, s: got["files"].append((n, s)))
    a.file_chunk_received.connect(lambda d: got["chunks"].append(d))
    a.disconnected.connect(
        lambda: got.__setitem__("a_disconnected", got["a_disconnected"] + 1)
    )
    b.disconnected.connect(
        lambda: got.__setitem__("b_disconnected", got["b_disconnected"] + 1)
    )

    # Baglanti + istek/cevap
    b.connect_to("127.0.0.1", a.port)
    assert b.send_request("Bilgisayar Yönetimi")
    assert wait_for(lambda: got["requests"] == [("Bilgisayar Yönetimi", "2222")])
    assert a.send_answer(True, "Bilgisayar Yönetimi")
    assert wait_for(
        lambda: got["answers"] == [(True, "Bilgisayar Yönetimi", "1111", "")]
    )
    print("PASS request/answer")

    # Frame, mouse, dosya mesajlari
    fake_jpeg = b"\xff\xd8" + os.urandom(5000)
    assert a.send_frame(fake_jpeg)
    assert b.send_mouse_move(10, 20)
    assert b.send_mouse_left()
    assert b.send_file_meta("odev.pdf", 5)
    assert b.send_file_chunk(b"hello")
    assert wait_for(lambda: got["frames"] == [fake_jpeg])
    assert wait_for(lambda: got["mouse"] == [(10, 20)])
    assert wait_for(lambda: got["clicks"] == ["left"])
    assert wait_for(lambda: got["files"] == [("odev.pdf", 5)])
    assert wait_for(lambda: got["chunks"] == [b"hello"])
    print("PASS frame/mouse/file")

    # Mesgulken gelen ucuncu baglanti otomatik reddedilir
    c = Peer("3333")
    c_answers = []
    c.answer_received.connect(lambda ok, mode, pid, why: c_answers.append((ok, why)))
    c.connect_to("127.0.0.1", a.port)
    assert wait_for(lambda: c_answers == [(False, "busy")])
    print("PASS busy reject")

    # Bilerek kapatan taraf sinyal almaz, karsi taraf alir
    b.close_connection()
    assert wait_for(lambda: got["a_disconnected"] == 1)
    assert not wait_for(lambda: got["b_disconnected"] > 0, timeout=0.5)
    assert wait_for(lambda: not a.connected)
    print("PASS disconnect")

    # Oturum bittikten sonra yeni baglanti kabul edilebilmeli
    d = Peer("4444")
    d.connect_to("127.0.0.1", a.port)
    assert d.send_request("Dosya Transferi")
    assert wait_for(lambda: ("Dosya Transferi", "4444") in got["requests"])
    print("PASS reconnect after session")

    for p in (a, b, c, d):
        p.shutdown()


def test_discovery():
    d1 = Discovery("1111", 40001)
    d2 = Discovery("2222", 40002)
    seen1, seen2 = [], []
    d1.peers_changed.connect(lambda peers: seen1.append(peers))
    d2.peers_changed.connect(lambda peers: seen2.append(peers))
    ok = wait_for(
        lambda: any("2222" in s for s in seen1) and any("1111" in s for s in seen2),
        timeout=6.0,
    )
    assert ok, "UDP kesfi calismadi (guvenlik duvari broadcast'i engelliyor olabilir)"
    entry = next(s for s in seen1 if "2222" in s)["2222"]
    assert entry["port"] == 40002
    assert entry["status"] == "available"

    # Durum degisikligi aninda duyurulur
    d2.set_status("busy")
    ok = wait_for(
        lambda: any(s.get("2222", {}).get("status") == "busy" for s in seen1),
        timeout=3.0,
    )
    assert ok, "durum degisikligi yayilmadi"
    print("PASS discovery")
    d1.stop()
    d2.stop()


if __name__ == "__main__":
    app = QCoreApplication(sys.argv)
    test_framing()
    test_peer_session()
    test_discovery()
    print("TUM TESTLER GECTI")
