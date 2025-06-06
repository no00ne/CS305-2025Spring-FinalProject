from flask import Flask, jsonify, request
from threading import Thread
from peer_manager import peer_status, rtt_tracker, blacklist
from transaction import get_recent_transactions, TransactionMessage, add_transaction
from link_simulator import rate_limiter
from message_handler import get_redundancy_stats
from outbox import get_outbox_status, gossip_message
from peer_discovery import known_peers
import json
from block_handler import received_blocks

app = Flask(__name__)
blockchain_data_ref = None
known_peers_ref = None
self_id = None

def start_dashboard(peer_id, port):
    global blockchain_data_ref, known_peers_ref, self_id
    blockchain_data_ref = received_blocks
    known_peers_ref = known_peers
    self_id = peer_id
    def run():
        app.run(host="0.0.0.0", port=port)
    Thread(target=run, daemon=True).start()

@app.route('/')
def home():
    return "Block P2P Network Simulation"

@app.route('/health')
def health():
    return 'OK'

@app.route('/blocks')
def blocks():
    return jsonify(blockchain_data_ref)

@app.route('/peers')
def peers():
    data = []
    for pid, (ip, port) in known_peers_ref.items():
        status = peer_status.get(pid, 'UNKNOWN')
        data.append({"id": pid, "ip": ip, "port": port, "status": status})
    return jsonify(data)

@app.route('/transactions')
def transactions():
    return jsonify(get_recent_transactions())

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    data = request.get_json(force=True)
    if 'id' in data:
        tx = data
    else:
        recipient = data.get('recipient')
        amount = data.get('amount', 0)
        tx = TransactionMessage(self_id, recipient, amount).to_dict()
    add_transaction(tx)
    gossip_message(self_id, tx)
    return jsonify({'id': tx['id']})

@app.route('/latency')
def latency():
    return jsonify(rtt_tracker)

@app.route('/capacity')
def capacity():
    return jsonify({"capacity": rate_limiter.capacity})

@app.route('/orphans')
def orphan_blocks():
    from block_handler import orphan_blocks
    return jsonify(orphan_blocks)

@app.route('/queue')
def message_queue():
    return jsonify(get_outbox_status())

@app.route('/redundancy')
def redundancy_stats():
    return jsonify({"redundant": get_redundancy_stats()})

@app.route('/blacklist')
def blacklist_display():
    return jsonify(list(blacklist))


