import threading
import time
import json
from collections import defaultdict


peer_status = {} # {peer_id: 'ALIVE', 'UNREACHABLE' or 'UNKNOWN'}
last_ping_time = {} # {peer_id: timestamp}
rtt_tracker = {} # {peer_id: transmission latency}

# === Check if peers are alive ===

def start_ping_loop(self_id, peer_table):
    from outbox import enqueue_message
    for pid in peer_table:
        if pid != self_id:
            rtt_tracker[pid] = None
            peer_status.setdefault(pid, 'UNKNOWN')
    def loop():
       while True:
           msg = {"type": "PING", "sender": self_id, "timestamp": time.time()}
           for pid, (ip, port) in peer_table.items():
               if pid == self_id:
                   continue
               enqueue_message(pid, ip, port, msg)
           time.sleep(5)
    threading.Thread(target=loop, daemon=True).start()

def create_pong(sender, recv_ts):
    return {"type": "PONG", "sender": sender, "timestamp": recv_ts}

def handle_pong(msg):
    sender = msg.get("sender")
    ts = msg.get("timestamp")
    if sender is None or ts is None:
        return
    rtt = time.time() - ts
    rtt_tracker[sender] = rtt
    update_peer_heartbeat(sender)


def start_peer_monitor():
    import threading
    def loop():
        while True:
            now = time.time()
            for pid, ts in list(last_ping_time.items()):
                if now - ts > 15:
                    peer_status[pid] = 'UNREACHABLE'
                else:
                    peer_status[pid] = 'ALIVE'
            time.sleep(5)
    threading.Thread(target=loop, daemon=True).start()

def update_peer_heartbeat(peer_id):
    last_ping_time[peer_id] = time.time()


# === Blacklist Logic ===

blacklist = set() # The set of banned peers

peer_offense_counts = {} # The offence times of peers

def record_offense(peer_id):
    count = peer_offense_counts.get(peer_id, 0) + 1
    peer_offense_counts[peer_id] = count
    if count > 3:
        blacklist.add(peer_id)

