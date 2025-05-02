
import time
import hashlib
import json
import uuid
from tx_pool import get_recent_transactions, clear_pool
from peer_discovery import is_light_node, known_peers

received_blocks = [] # the structure of local blockchain

def create_dummy_block(peer_id, MALICIOUS_MODE):
    # TODO: Define the JSON format of a block, which should include {type: Block, Block Generator’s ID, Timestamp, Block Height, Block ID, ID of Block’s Parent, and Transactions}. 
    # The block ID is the hash value of block structure except for the item of the block ID. 
    # A new block’s parent is the last block in the blockchain, to which the new block will be linked. 
    # The height of a block is the height of its parent plus one. 
    # If the block generator is malicious, it can generate random block ID. 

    # TODO: Read the transactions in the local pool using the function get_recent_transactions and create a new block.

    # TODO: Clear the local transaction pool and add the new block into the local blockchain in receive_block.
    pass
    return block



