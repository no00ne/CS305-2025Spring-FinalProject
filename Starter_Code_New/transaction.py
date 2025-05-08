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
        # TODO: Randomly choose a peer from `known_peers` and generate a transaction to transfer arbitrary amount of money to the peer.

        # TODO:  Add the transaction to local `tx_pool` using the function `add_transaction`.

        # TODO:  Broadcast the transaction to `known_peers` using the function `gossip_message` in `outbox.py`.

        pass
    threading.Thread(target=loop, daemon=True).start()

def add_transaction(tx):
    # TODO: Add a transaction to the local `tx_pool` if it is in the pool.

    # TODO: Add the transaction ID to `tx_ids`.
    pass

def get_recent_transactions():
    # TODO: Return all transactions in the local `tx_pool`.
    pass

def clear_pool():
    # Remove all transactions in `tx_pool` and transaction IDs in `tx_ids`.

    pass