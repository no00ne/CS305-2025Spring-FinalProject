
import threading
import time
import json
from collections import defaultdict, deque
from network.peer_manager import is_banned, ban_peer
from network.link_simulator import relay_or_direct_send

# === Per-peer Rate Limiting ===
RATE_LIMIT = 10  # max messages
TIME_WINDOW = 10  # per seconds
peer_send_timestamps = defaultdict(list)

def is_rate_limited(peer_id):
    # TODO: Check how many messages were sent from the peer to a target peer during the TIME_WINDOW that ends now.
    # TODO: Check if the sending frequency exceeds the sending rate limit RATE_LIMIT.
    # TODO: Record the current sending time into peer_send_timestamps.
    pass

MAX_RETRIES = 3
RETRY_INTERVAL = 5  # seconds
QUEUE_LIMIT = 50

# Priority levels
PRIORITY_HIGH = {"BLOCK", "INV", "GETDATA"}
PRIORITY_MEDIUM = {"TX", "HELLO"}
PRIORITY_LOW = {"PING", "PONG"}

# Queues per peer and priority
queues = defaultdict(lambda: defaultdict(deque))
retries = defaultdict(int)
lock = threading.Lock()

def classify_priority(message):
    # TODO: Classify the priority of a message based on the message type.
    pass

def enqueue_message(target_id, ip, port, message):
    # TODO: Check if the sender sends message to the receiver too frequently. If you, drop the message.
    # TODO: Check if the receiver is banned.
    # TODO: Classify the priority of the sending messages based on the message type.
    # TODO: Add the message to the queue if the length of the queue is within the limit QUEUE_LIMIT, or otherwise, drop the message.

    pass

def send_from_queue(self_id, send_func):
    def worker():
        # TODO: Read the message in the queue. Each time, read a target peer’s message with the highest priority. Then, move to the next target peer’s message. This can ensure the fairness of sending messages to different target peers.
        # TODO: Check sending the message to the target peer directly or through a relaying node using the function relay_or_direct_send.
        # TODO: Retry a message if it is sent unsuccessfully and drop the message if the number of retry exceed the limit MAX_RETRIES.
        pass
    threading.Thread(target=worker, daemon=True).start()

def get_outbox_status():
    # TODO: Read the sending message in the queues.
    pass
