import random
import time
import json
from threading import Lock
import peer_discovery
from peer_discovery import known_peers, peer_flags
from network.peer_manager import rtt_tracker

# === Network Simulation Config ===
DROP_PROB = 0.05
LATENCY_MS = (20, 100)
SEND_RATE_LIMIT = 5  # messages per second



# === Relay Logic ===
def get_relay_peer(self_id, dst_id):
    # TODO: Read the latency between the sender and other peers in rtt_tracker in peer_manager.py.
    # TODO: Find the set of relay candidates reachable from the target peer. 
    # TODO: Select the best relaying peers with the smallest latency.

    pass

    return best_peer  # (peer_id, ip, port) or None

def relay_or_direct_send(self_id, dst_id, message, send_func):
    # TODO: Check if the target peer is NATed. If yes, use the function get_relay_peer to find the best relaying peer.
    # TODO: Send the message to the target peer or relaying peer using the function send_message.

    pass