import json
import socket
import threading
import argparse
import time
import random
import gossip
from gossip import gossip_random_subset
from peer_discovery import start_peer_discovery, known_peers
from utils import generate_message_id
from block_handler import create_dummy_block, received_blocks
from message_handler import dispatch_message, cleanup_seen_messages
from network.socket_server import start_socket_server
from dashboard import start_dashboard
from messages.transaction_message import TransactionMessage
from messages.ping import start_ping_loop
from network.peer_manager import start_peer_monitor
from network.outbox import send_from_queue, enqueue_message
from network.link_simulator import apply_network_conditions, start_dynamic_capacity_adjustment
from messages.inv_message import create_inv

RECV_BUFFER = 4096
server_socket = None  # global
self_ip = None
self_port = None
connection_handler = None

def send_message(ip, port, message):
    # TODO: Send the message to the target peer.
    pass

def listen_on_port(self_id, self_ip, port):
    def handler(conn, addr):
        # TODO: Pass the received data to the function dispatch_message for message processing.
        pass
    threading.Thread(target=start_socket_server, args=(self_ip, port, handler), daemon=True).start()
    return handler

def start_block_generation(self_id, MALICIOUS_MODE, interval=20):
    def mine():
        # TODO: Exploit the function create_dummy_block to generate blocks periodically.
        # TODO: Create an “INV” message for the new blocks.
        # TODO: Send the “INV” message to known peers and put the messages into the outbox queue.
        pass
    threading.Thread(target=mine, daemon=True).start()

def start_transaction_broadcast(self_id, interval=15):
    def loop():
        # TODO: Generate the set of transactions with random senders and receivers (selected from known peers).
        # TODO: Broadcast the transactions to known peers based on gossip, and put the message into the outbox queue.
        pass
    threading.Thread(target=loop, daemon=True).start()

def request_block_sync(self_id):
    # TODO: Define the JSON structure of a “GET_BLOCK_HEADERS” message, which should include: {message type, from_id}. from_id is the sender’s alias.
    # TODO: Send a “GET_BLOCK_HEADERS” message to all known peers and put the messages into the outbox queue.
    pass

def main():

    # Input the peer's configuration from command line.
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--fanout", type=int, help="Override fanout for this peer")
    parser.add_argument("--mode", default="normal", help="Node mode: normal or malicious")
    args = parser.parse_args()
    MALICIOUS_MODE = args.mode == 'malicious'

    # Read the peer's configuration from config.json
    self_id = args.id
    with open(args.config) as f:
        config = json.load(f)

    self_info = config["peers"][self_id]

    from peer_discovery import peer_flags
    peer_flags[self_id] = {
        "nat": self_info.get("nat", False),
        "light": self_info.get("light", False)
    }
    light_mode = self_info.get('light', False)
    for peer_id, peer_info in config["peers"].items():
        known_peers[peer_id] = (peer_info["ip"], peer_info["port"])
    gossip.peer_config = config["peers"]
    if args.fanout:
        gossip.peer_config[self_id]["fanout"] = args.fanout
        print(f"[INFO] Overriding fanout to {args.fanout}")

    ip = self_info["ip"]
    port = self_info["port"]

    # Start listening on port
    handler = listen_on_port(self_id, ip, port) 

    # Start peer discovery
    start_peer_discovery(self_id, self_info, send_message)

    # Start synchronizing the latest blockchain
    threading.Thread(target=request_block_sync, args=(self_id,), daemon=True).start()

    # Start transaction and block generation
    if not light_mode:
        start_transaction_broadcast(self_id)
        start_block_generation(self_id, MALICIOUS_MODE)

    # Send messages in the ourbox queue to target peers 
    send_from_queue(self_id, send_message) 

    print(f"[{self_id}] Node running at {ip}:{port}")
    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()