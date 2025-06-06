import time
import json
import hashlib
import random
import threading
from peer_discovery import known_peers
from outbox import gossip_message

class TransactionMessage:
    def __init__(self, sender, receiver, amount, timestamp=None):
        self.type = "TX"
        self.from_peer = sender
        self.to_peer = receiver
        self.amount = amount
        self.timestamp = timestamp if timestamp else time.time()
        self.id = self.compute_hash()

    def compute_hash(self):
        tx_data = {
            "type": self.type,
            "from": self.from_peer,
            "to": self.to_peer,
            "amount": self.amount,
            "timestamp": self.timestamp
        }
        return hashlib.sha256(json.dumps(tx_data, sort_keys=True).encode()).hexdigest()

    def to_dict(self):
        return {
            "type": self.type,
            "id": self.id,
            "from": self.from_peer,
            "to": self.to_peer,
            "amount": self.amount,
            "timestamp": self.timestamp
        }

    @staticmethod
    def from_dict(data):
        return TransactionMessage(
            sender=data["from"],
            receiver=data["to"],
            amount=data["amount"],
            timestamp=data["timestamp"]
        )
    
tx_pool = [] # local transaction pool
tx_ids = set() # the set of IDs of transactions in the local pool
    
def transaction_generation(self_id, interval=15):
    def loop():
        while True:
            peers = [p for p in known_peers.keys() if p != self_id]
            if not peers:
                time.sleep(interval)
                continue
            target = random.choice(peers)
            amount = random.randint(1, 100)
            tx = TransactionMessage(self_id, target, amount)
            add_transaction(tx.to_dict())
            gossip_message(self_id, tx.to_dict())
            time.sleep(interval)
    threading.Thread(target=loop, daemon=True).start()

def add_transaction(tx):
    if tx["id"] in tx_ids:
        return
    tx_pool.append(tx)
    tx_ids.add(tx["id"])

def get_recent_transactions():
    return list(tx_pool)

def clear_pool():
    # Remove all transactions in `tx_pool` and transaction IDs in `tx_ids`.
    tx_pool.clear()
    tx_ids.clear()
