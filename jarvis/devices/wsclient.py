"""A minimal RFC 6455 WebSocket client (text frames only), standard library. Just enough to talk to a TV."""
import base64
import os
import socket
import ssl
import struct


class WSError(OSError):
    pass


class WebSocket:
    def __init__(self, host, port, path, use_ssl=True, timeout=5.0):
        self.host, self.port, self.path, self.use_ssl, self.timeout = host, port, path, use_ssl, timeout
        self.sock = None

    def connect(self):
        raw = socket.create_connection((self.host, self.port), timeout=self.timeout)
        if self.use_ssl:
            # Samsung TVs present a self-signed certificate, so it cannot be verified against a CA.
            # This is only ever used for a direct connection to a TV on your own LAN.
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            raw = ctx.wrap_socket(raw, server_hostname=self.host)
        self.sock = raw
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((
            f"GET {self.path} HTTP/1.1\r\nHost: {self.host}:{self.port}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = self.sock.recv(1024)
            if not chunk:
                raise WSError("connection closed during handshake")
            head += chunk
        if b" 101 " not in head.split(b"\r\n", 1)[0] + b" ":
            raise WSError("websocket handshake refused: " + head.split(b"\r\n", 1)[0].decode(errors="replace"))
        self._buffer = head.split(b"\r\n\r\n", 1)[1]

    def _read(self, n):
        while len(self._buffer) < n:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise WSError("connection closed")
            self._buffer += chunk
        out, self._buffer = self._buffer[:n], self._buffer[n:]
        return out

    def _frame(self, opcode, payload: bytes):
        n = len(payload)
        head = bytes([0x80 | opcode])
        if n < 126:
            head += bytes([0x80 | n])
        elif n < 65536:
            head += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            head += bytes([0x80 | 127]) + struct.pack(">Q", n)
        mask = os.urandom(4)
        return head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload))

    def send_text(self, text: str):
        self.sock.sendall(self._frame(0x1, text.encode()))

    def recv_text(self) -> str:
        """Next text message (answers pings, raises WSError on close)."""
        data = b""
        while True:
            b1, b2 = self._read(2)
            opcode, n = b1 & 0x0F, b2 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            mask = self._read(4) if b2 & 0x80 else None
            payload = self._read(n)
            if mask:
                payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
            if opcode == 0x8:
                raise WSError("closed by TV")
            if opcode == 0x9:
                self.sock.sendall(self._frame(0xA, payload))
                continue
            if opcode == 0xA:
                continue
            data += payload
            if b1 & 0x80:
                return data.decode("utf-8", "replace")

    def close(self):
        try:
            if self.sock:
                self.sock.sendall(self._frame(0x8, b""))
                self.sock.close()
        except OSError:
            pass
        self.sock = None
