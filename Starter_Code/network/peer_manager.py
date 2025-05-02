
import time
from collections import defaultdict

peer_status = {}
last_ping_time = {}
relay_score = defaultdict(int)
rtt_tracker = {}
retry_failures = defaultdict(int)
OFFENCE_LIMIT = 3

# === Blacklist Logic ===

blacklist = set()

peer_offense_counts = {}

def record_offense(peer_id):
    # TODO: Record the offence when detecting malicious behavior of a peer.
    # TODO: Ban the peer using the function Ban_peer if the number of offences exceeds the limit OFFENCE_LIMIT.
    pass

def ban_peer(peer_id):
    # TODO: Add a peer to the blacklist.
    pass

def is_banned(peer_id):
    # TODO: Check if a peer is in the blacklist.
    pass
