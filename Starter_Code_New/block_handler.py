
import time
import hashlib
import json
import threading
from transaction import get_recent_transactions, clear_pool
from peer_discovery import known_peers, peer_config

from outbox import  enqueue_message, gossip_message
from utils import generate_message_id
from peer_manager import record_offense

received_blocks = [] # The local blockchain. The blocks are added linearly at the end of the set.
header_store = [] # The header of blocks in the local blockchain. Used by lightweight peers.
orphan_blocks = {} # The block whose previous block is not in the local blockchain. Waiting for the previous block.

def request_block_sync(self_id):
    # TODO: Define the JSON format of a `GET_BLOCK_HEADERS`, which should include `{message type, sender's ID}`.

    # TODO: Send a `GET_BLOCK_HEADERS` message to each known peer and put the messages in the outbox queue.
    pass

def block_generation(self_id, MALICIOUS_MODE, interval=20):
    from inv_message import create_inv
    def mine():

    # TODO: Create a new block periodically using the function `create_dummy_block`.

    # TODO: Create an `INV` message for the new block using the function `create_inv` in `inv_message.py`.

    # TODO: Broadcast the `INV` message to known peers using the function `gossip` in `outbox.py`.
        pass
    threading.Thread(target=mine, daemon=True).start()

def create_dummy_block(peer_id, MALICIOUS_MODE):

    # TODO: Define the JSON format of a `block`, which should include `{message type, peer's ID, timestamp, block ID, previous block's ID, and transactions}`. 
    # The `block ID` is the hash value of block structure except for the item `block ID`. 
    # `previous block` is the last block in the blockchain, to which the new block will be linked. 
    # If the block generator is malicious, it can generate random block ID.

    # TODO: Read the transactions in the local `tx_pool` using the function `get_recent_transactions` in `transaction.py`.

    # TODO: Create a new block with the transactions and generate the block ID using the function `compute_block_hash`.
     
    # TODO: Clear the local transaction pool and add the new block into the local blockchain (`receive_block`).
    pass
    return block

def compute_block_hash(block):
    # TODO: Compute the hash of a block except for the term `block ID`.
    pass

def handle_block(msg, self_id):
    # TODO: Check the correctness of `block ID` in the received block. If incorrect, drop the block and record the sender's offence.

    # TODO: Check if the block exists in the local blockchain. If yes, drop the block.

    # TODO: Check if the previous block of the block exists in the local blockchain. If not, add the block to the list of orphaned blocks (`orphan_blocks`). If yes, add the block to the local blockchain.

    # TODO: Check if the block is the previous block of blocks in `orphan_blocks`. If yes, add the orphaned blocks to the local blockchain.
    pass


def create_getblock(sender_id, requested_ids):
    # TODO: Define the JSON format of a `GETBLOCK` message, which should include `{message type, sender's ID, requesting block IDs}`.
    pass


def get_block_by_id(block_id):
    # TODO: Return the block in the local blockchain based on the block ID.
    pass



