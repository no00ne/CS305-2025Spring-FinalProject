import time
import json
from utils import generate_message_id
from outbox import gossip_message

def create_inv(sender_id, block_ids):
    return {
        "type": "INV",
        "sender": sender_id,
        "blocks": block_ids,
        "id": generate_message_id(),
    }

def get_inventory():
    from block_handler import received_blocks
    return [b["block_id"] for b in received_blocks]

def broadcast_inventory(self_id):
    inv = create_inv(self_id, get_inventory())
    gossip_message(self_id, inv)


