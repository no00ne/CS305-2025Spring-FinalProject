
import time
import hashlib
import json
import threading
from transaction import get_recent_transactions, clear_pool
from peer_discovery import known_peers, peer_config, peer_flags

from outbox import  enqueue_message, gossip_message
from utils import generate_message_id
from peer_manager import record_offense

received_blocks = [] # The local blockchain. The blocks are added linearly at the end of the set.
header_store = [] # The header of blocks in the local blockchain. Used by lightweight peers.
orphan_blocks = {} # The block whose previous block is not in the local blockchain. Waiting for the previous block.

def init_genesis_block():
    """Create the genesis block and populate local stores."""
    block = {
        "type": "BLOCK",
        "peer": "GENESIS",
        "timestamp": time.time(),
        "prev_id": None,
        "transactions": [],
    }
    block_id = compute_block_hash(block)
    block["block_id"] = block_id
    received_blocks.append(block)
    header_store.append({"block_id": block_id, "prev_id": None, "timestamp": block["timestamp"]})


def request_block_sync(self_id):
    msg = {"type": "GET_BLOCK_HEADERS", "sender": self_id}
    for peer_id, (ip, port) in known_peers.items():
        if peer_id == self_id:
            continue
        enqueue_message(peer_id, ip, port, msg)

def block_generation(self_id, MALICIOUS_MODE, interval=10):
    from inv_message import create_inv
    def mine():
        while True:
            block = create_dummy_block(self_id, MALICIOUS_MODE)
            inv = create_inv(self_id, [block["block_id"]])
            gossip_message(self_id, inv)
            time.sleep(interval)
    threading.Thread(target=mine, daemon=True).start()

def create_dummy_block(peer_id, MALICIOUS_MODE):

    # TODO: Define the JSON format of a `block`, which should include `{message type, peer's ID, timestamp, block ID, previous block's ID, and transactions}`. 
    # The `block ID` is the hash value of block structure except for the item `block ID`. 
    # `previous block` is the last block in the blockchain, to which the new block will be linked. 
    # If the block generator is malicious, it can generate random block ID.

    txs = get_recent_transactions()
    prev_id = received_blocks[-1]["block_id"] if received_blocks else None
    block = {
        "type": "BLOCK",
        "peer": peer_id,
        "timestamp": time.time(),
        "prev_id": prev_id,
        "transactions": txs,
    }
    if MALICIOUS_MODE:
        block_id = generate_message_id()
    else:
        block_id = compute_block_hash(block)
    block["block_id"] = block_id
    clear_pool()
    receive_block(block)
    return block

def compute_block_hash(block):
    temp = dict(block)
    temp.pop("block_id", None)
    return hashlib.sha256(json.dumps(temp, sort_keys=True).encode()).hexdigest()

def receive_block(block, light=False):
    block_id = block.get("block_id")
    if compute_block_hash(block) != block_id:
        record_offense(block.get("peer"))
        return False
    if any(b["block_id"] == block_id for b in received_blocks):
        return False
    prev = block.get("prev_id")
    if prev and not any(b["block_id"] == prev for b in received_blocks):
        orphan_blocks[block_id] = block
        return False
    if not light:
        received_blocks.append(block)
    header_store.append({"block_id": block_id, "prev_id": prev, "timestamp": block["timestamp"]})
    to_attach = [oid for oid, ob in list(orphan_blocks.items()) if ob.get("prev_id") == block_id]
    for oid in to_attach:
        ob = orphan_blocks.pop(oid)
        if not light:
            received_blocks.append(ob)
        header_store.append({"block_id": oid, "prev_id": ob.get("prev_id"), "timestamp": ob["timestamp"]})
    return True

def handle_block(msg, self_id):
    """Validate and store a received block."""
    light = peer_flags.get(self_id, {}).get("light", False)
    receive_block(msg, light)


def create_getblock(sender_id, requested_ids):
    return {"type": "GETBLOCK", "sender": sender_id, "blocks": requested_ids}


def get_block_by_id(block_id):
    for blk in received_blocks:
        if blk.get("block_id") == block_id:
            return blk
    return None



