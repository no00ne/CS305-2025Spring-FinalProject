import json, time, threading
from utils import generate_message_id


known_peers = {}        # { peer_id: (ip, port) }
peer_flags = {}         # { peer_id: { 'nat': True/False, 'light': True/False } }
reachable_by = {}       # { peer_id: { set of peer_ids who can reach this peer }}
peer_config={}

def start_peer_discovery(self_id, self_info):
    from outbox import enqueue_message
    def loop():
        hello = {
            "type": "HELLO",
            "sender": self_id,
            "ip": self_info.get("ip"),
            "port": self_info.get("port"),
            "flags": peer_flags.get(self_id, {}),
            "id": generate_message_id(),
        }

        for peer_id, (ip, port) in known_peers.items():
            if peer_id == self_id:
                continue
            # NAT rules: only peers in the same local network can reach each other
            if self_info.get("nat") and peer_config.get(peer_id, {}).get("localnetworkid") != self_info.get("localnetworkid"):
                continue
            enqueue_message(peer_id, ip, port, hello)
    threading.Thread(target=loop, daemon=True).start()

def handle_hello_message(msg, self_id):
    new_peers = []

    sender = msg.get("sender")
    ip = msg.get("ip")
    port = msg.get("port")
    flags = msg.get("flags", {})

    if sender not in known_peers:
        known_peers[sender] = (ip, port)
        peer_flags[sender] = flags
        new_peers.append(sender)

    reachable_by.setdefault(sender, set()).add(self_id)

    return new_peers

    return new_peers 


