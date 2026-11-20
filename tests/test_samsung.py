import base64
import hashlib
import json
import socket
import struct
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from jarvis.devices import tv


class FakeSamsung:
    """A just-enough Samsung remote server: real WebSocket handshake + framing, no TLS."""

    def __init__(self, allow=True, token="12345678"):
        self.allow, self.token = allow, token
        self.requests, self.keys = [], []
        self.srv = socket.socket()
        self.srv.bind(("127.0.0.1", 0))
        self.srv.listen(5)
        self.port = self.srv.getsockname()[1]
        threading.Thread(target=self._loop, daemon=True).start()

    def _frame(self, text):
        p = text.encode()
        return bytes([0x81, len(p)]) + p  # server frames are unmasked

    def _loop(self):
        while True:
            try:
                c, _ = self.srv.accept()
            except OSError:
                return
            threading.Thread(target=self._serve, args=(c,), daemon=True).start()

    def _serve(self, c):
        data = b""
        while b"\r\n\r\n" not in data:
            data += c.recv(1024)
        head = data.decode()
        self.requests.append(head.split("\r\n")[0])
        key = [l.split(": ")[1] for l in head.split("\r\n") if l.lower().startswith("sec-websocket-key")][0]
        accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        c.sendall(f"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {accept}\r\n\r\n".encode())
        ev = {"event": "ms.channel.connect", "data": {"token": self.token}} if self.allow else {"event": "ms.channel.timeOut"}
        c.sendall(self._frame(json.dumps(ev)))
        if not self.allow:
            return
        try:
            while True:
                h = c.recv(2)
                if len(h) < 2:
                    return
                n = h[1] & 0x7F
                if n == 126:
                    n = struct.unpack(">H", c.recv(2))[0]
                mask = c.recv(4)
                payload = b""
                while len(payload) < n:
                    payload += c.recv(n - len(payload))
                msg = json.loads(bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))
                self.keys.append(msg["params"]["DataOfCmd"])
        except OSError:
            return


def make(fake, **kw):
    return tv.SamsungTV("127.0.0.1", port=fake.port, use_ssl=False, token_file=Path(tempfile.mkdtemp()) / "t.json", timeout=2, **kw)


def wait(cond, secs=2):
    import time
    end = time.time() + secs
    while time.time() < end and not cond():
        time.sleep(0.01)


class Samsung(unittest.TestCase):
    def test_keys_reach_the_tv_and_token_is_saved(self):
        fake = FakeSamsung()
        t = make(fake)
        self.assertEqual(t.send("volume_up"), "Samsung: volume_up")
        self.assertEqual(t.send("mute"), "Samsung: mute")
        wait(lambda: len(fake.keys) == 2)
        self.assertEqual(fake.keys, ["KEY_VOLUP", "KEY_MUTE"])
        self.assertEqual(len(fake.requests), 1, "one connection is reused")
        q = parse_qs(urlparse(fake.requests[0].split()[1]).query)
        self.assertEqual(base64.b64decode(q["name"][0]), b"Jarvis")
        self.assertEqual(json.loads(t.token_file.read_text()), {"127.0.0.1": "12345678"})

    def test_saved_token_is_sent_on_next_session(self):
        fake = FakeSamsung()
        t = make(fake)
        t.send("home")
        t2 = tv.SamsungTV("127.0.0.1", port=fake.port, use_ssl=False, token_file=t.token_file, timeout=2)
        t2.send("home")
        self.assertIn("token=12345678", fake.requests[1])

    def test_play_pause_alternates(self):
        fake = FakeSamsung()
        t = make(fake)
        for _ in range(3):
            t.send("play_pause")
        wait(lambda: len(fake.keys) == 3)
        self.assertEqual(fake.keys, ["KEY_PAUSE", "KEY_PLAY", "KEY_PAUSE"])

    def test_not_allowed_yet_gives_a_helpful_message(self):
        self.assertIn("choose Allow", make(FakeSamsung(allow=False)).send("home"))

    def test_reconnects_after_the_tv_drops_us(self):
        fake = FakeSamsung()
        t = make(fake)
        t.send("home")
        t.ws.sock.close()  # simulate a dropped connection
        self.assertEqual(t.send("back"), "Samsung: back")
        wait(lambda: "KEY_RETURN" in fake.keys)
        self.assertIn("KEY_RETURN", fake.keys)

    def test_off_tv_is_a_message_not_a_crash_and_power_falls_back_to_wol(self):
        from unittest import mock
        dead = tv.SamsungTV("127.0.0.1", mac="aa:bb:cc:dd:ee:ff", port=1, use_ssl=False,
                            token_file=Path(tempfile.mkdtemp()) / "t.json", timeout=0.3)
        self.assertIn("didn't answer", dead.send("home"))
        with mock.patch.object(tv, "wake_on_lan") as wol:
            self.assertIn("Wake-on-LAN", dead.send("power"))
        wol.assert_called_once_with("aa:bb:cc:dd:ee:ff")

    def test_wol_packet_shape(self):
        from unittest import mock
        with mock.patch("socket.socket") as sock:
            tv.wake_on_lan("aa:bb:cc:dd:ee:ff")
        pkt = sock.return_value.__enter__.return_value.sendto.call_args[0][0]
        self.assertEqual(len(pkt), 102)
        self.assertEqual(pkt[:6], b"\xff" * 6)
        with self.assertRaises(ValueError):
            tv.wake_on_lan("aa:bb")


if __name__ == "__main__":
    unittest.main()
