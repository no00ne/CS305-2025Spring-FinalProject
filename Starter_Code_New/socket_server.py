import socket
import threading
import time
import json
from message_handler import dispatch_message

RECV_BUFFER = 4096

def start_socket_server(self_id, self_ip, port):

    def listen_loop():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self_ip, port))
        sock.listen()
        while True:
            conn, _ = sock.accept()
            data = conn.recv(RECV_BUFFER)
            if not data:
                conn.close()
                continue
            try:
                msg = json.loads(data.decode())
                dispatch_message(msg, self_id, self_ip)
            except Exception:
                pass
            conn.close()

    # ✅ Run listener in background
    threading.Thread(target=listen_loop, daemon=True).start()

