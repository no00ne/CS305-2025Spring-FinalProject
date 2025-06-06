import socket
import threading
import time
import json
import random
from collections import defaultdict, deque
from threading import Lock

# === Per-peer Rate Limiting ===
RATE_LIMIT = 10  # max messages
TIME_WINDOW = 10  # per seconds
peer_send_timestamps = defaultdict(list) # the timestamps of sending messages to each peer

MAX_RETRIES = 3
RETRY_INTERVAL = 5  # seconds
QUEUE_LIMIT = 50

# Priority levels
PRIORITY_HIGH = {"PING", "PONG", "BLOCK", "INV", "GETDATA"}
PRIORITY_MEDIUM = {"TX", "HELLO"}
PRIORITY_LOW = {"RELAY"}

DROP_PROB = 0.05
LATENCY_MS = (20, 100)
SEND_RATE_LIMIT = 5  # messages per second

drop_stats = {
    "BLOCK": 0,
    "TX": 0,
    "HELLO": 0,
    "PING": 0,
    "PONG": 0,
    "OTHER": 0
}

# Queues per peer and priority
queues = defaultdict(lambda: defaultdict(deque))
retries = defaultdict(int)
lock = threading.Lock()

# === Sending Rate Limiter ===
class RateLimiter:
    def __init__(self, rate=SEND_RATE_LIMIT):
        self.capacity = rate               # Max burst size
        self.tokens = rate                # Start full
        self.refill_rate = rate           # Tokens added per second
        self.last_check = time.time()
        self.lock = Lock()

    def allow(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_check
            self.tokens += elapsed * self.refill_rate
            self.tokens = min(self.tokens, self.capacity)
            self.last_check = now

            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

rate_limiter = RateLimiter()

def enqueue_message(target_id, ip, port, message):
    from peer_manager import blacklist, rtt_tracker
    if is_rate_limited(target_id):
        return
    if target_id in blacklist:
        return
    priority = classify_priority(message)
    with lock:
        q = queues[target_id][priority]
        if len(q) < QUEUE_LIMIT:
            q.append((ip, port, message))


def is_rate_limited(peer_id):
    now = time.time()
    timestamps = peer_send_timestamps[peer_id]
    timestamps[:] = [t for t in timestamps if now - t < TIME_WINDOW]
    if len(timestamps) >= RATE_LIMIT:
        return True
    timestamps.append(now)
    return False

def classify_priority(message):
    mtype = message.get("type")
    if mtype in PRIORITY_HIGH:
        return "high"
    if mtype in PRIORITY_MEDIUM:
        return "medium"
    return "low"
    

def send_from_queue(self_id):
    def worker():
        while True:
            sent = False
            with lock:
                for peer_id in list(queues.keys()):
                    q_levels = queues[peer_id]
                    message_tuple = None
                    for level in ["high", "medium", "low"]:
                        if q_levels[level]:
                            message_tuple = q_levels[level].popleft()
                            break
                    if message_tuple:
                        ip, port, msg = message_tuple
                        break
                else:
                    message_tuple = None
            if message_tuple:
                success = relay_or_direct_send(self_id, peer_id, msg)
                if not success:
                    key = (peer_id, msg.get("id"))
                    retries[key] += 1
                    if retries[key] < MAX_RETRIES:
                        enqueue_message(peer_id, ip, port, msg)
                    else:
                        retries.pop(key, None)
                sent = True
            if not sent:
                time.sleep(0.1)
    threading.Thread(target=worker, daemon=True).start()

def relay_or_direct_send(self_id, dst_id, message):
    from peer_discovery import known_peers, peer_flags

    nat = peer_flags.get(dst_id, {}).get("nat", False)
    if nat:
        relay = get_relay_peer(self_id, dst_id)
        if not relay:
            return False
        relay_id, ip, port = relay
        relay_msg = {
            "type": "RELAY",
            "sender": self_id,
            "target": dst_id,
            "payload": message,
        }
        return send_message(ip, port, relay_msg)
    else:
        ip, port = known_peers.get(dst_id, (None, None))
        if ip is None:
            return False
        return send_message(ip, port, message)

def get_relay_peer(self_id, dst_id):
    from peer_manager import  rtt_tracker
    from peer_discovery import known_peers, reachable_by
    candidates = reachable_by.get(dst_id, set())
    best_peer = None
    best_latency = float('inf')
    for pid in candidates:
        if pid == self_id or pid not in known_peers:
            continue

        lat = rtt_tracker.get(pid)
        if lat is None:
            continue
        if lat < best_latency:
            best_peer = pid
            best_latency = lat
    if best_peer is not None:

        ip, port = known_peers[best_peer]
        return best_peer, ip, port
    return None

def send_message(ip, port, message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, port))
            s.sendall(json.dumps(message).encode())
        return True
    except Exception:
        return False


def apply_network_conditions(send_func):
    def wrapper(ip, port, message):
        mtype = message.get("type", "OTHER")
        if not rate_limiter.allow():
            drop_stats[mtype] = drop_stats.get(mtype, 0) + 1
            return False
        if random.random() < DROP_PROB:
            drop_stats[mtype] = drop_stats.get(mtype, 0) + 1
            return False
        time.sleep(random.randint(*LATENCY_MS)/1000)
        return send_func(ip, port, message)
    return wrapper

send_message = apply_network_conditions(send_message)

def start_dynamic_capacity_adjustment():
    def adjust_loop():
        while True:
            new_cap = random.randint(2, 10)
            rate_limiter.capacity = new_cap
            rate_limiter.refill_rate = new_cap
            time.sleep(5)
    threading.Thread(target=adjust_loop, daemon=True).start()


def gossip_message(self_id, message, fanout=3):


    from peer_discovery import known_peers, peer_config, peer_flags


    fanout = peer_config.get(self_id, {}).get("fanout", fanout)
    peers = list(known_peers.keys())
    if message.get("type") == "TX":
        peers = [p for p in peers if not peer_flags.get(p, {}).get("light")]
    random.shuffle(peers)
    targets = peers[:fanout]
    for pid in targets:
        ip, port = known_peers[pid]
        enqueue_message(pid, ip, port, message)

def get_outbox_status():
    status = {}
    with lock:
        for pid, lvl in queues.items():
            status[pid] = {k: len(v) for k, v in lvl.items()}
    return status


def get_drop_stats():
    return drop_stats

