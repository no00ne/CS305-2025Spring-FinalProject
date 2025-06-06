import json
import threading
import time
import hashlib
import random
from collections import defaultdict
from peer_discovery import handle_hello_message, known_peers, peer_config, peer_flags
from block_handler import handle_block, get_block_by_id, create_getblock, received_blocks, header_store
from inv_message import  create_inv, get_inventory
from block_handler import create_getblock
from peer_manager import  update_peer_heartbeat, record_offense, create_pong, handle_pong
from transaction import add_transaction, verify_transaction
from outbox import enqueue_message, gossip_message


# === Global State ===
SEEN_EXPIRY_SECONDS = 600  # 10 minutes
seen_message_ids = {}
seen_txs = set()
redundant_blocks = 0
redundant_txs = 0
message_redundancy = 0
peer_inbound_timestamps = defaultdict(list)


# === Inbound Rate Limiting ===
INBOUND_RATE_LIMIT = 10
INBOUND_TIME_WINDOW = 10  # seconds

def is_inbound_limited(peer_id):
    now = time.time()
    timestamps = peer_inbound_timestamps[peer_id]
    timestamps[:] = [t for t in timestamps if now - t < INBOUND_TIME_WINDOW]
    if len(timestamps) >= INBOUND_RATE_LIMIT:
        return True
    timestamps.append(now)
    return False

# ===  Redundancy Tracking ===

def get_redundancy_stats():
    return message_redundancy

# === Main Message Dispatcher ===
def dispatch_message(msg, self_id, self_ip):
    
    msg_type = msg.get("type")

    msg_id = msg.get("id")
    sender = msg.get("sender")
    if msg_id in seen_message_ids:
        global message_redundancy
        message_redundancy += 1
        return
    seen_message_ids[msg_id] = time.time()
    if is_inbound_limited(sender):
        return
    from peer_manager import blacklist
    if sender in blacklist:
        return


    if msg_type == "RELAY":
        target = msg.get("target")
        if target == self_id:
            dispatch_message(msg.get("payload", {}), self_id, self_ip)
        else:
            ip, port = known_peers.get(target, (None, None))
            if ip:
                enqueue_message(target, ip, port, msg)

    elif msg_type == "HELLO":
        handle_hello_message(msg, self_id)

    elif msg_type == "BLOCK":

        block_id = msg.get("block_id")
        if any(b["block_id"] == block_id for b in received_blocks):
            global redundant_blocks
            redundant_blocks += 1
            return
        handle_block(msg, self_id)
        inv = create_inv(self_id, [block_id])

        gossip_message(self_id, inv)



    elif msg_type == "TX":
        if not verify_transaction(msg):
            record_offense(sender)
            return
        if msg.get("id") in seen_txs:
            global redundant_txs
            redundant_txs += 1
            return
        seen_txs.add(msg.get("id"))

        add_transaction(msg)
        gossip_message(self_id, msg)


    elif msg_type == "PING":
        update_peer_heartbeat(sender)
        pong = create_pong(self_id, msg.get("timestamp"))
        ip, port = known_peers.get(sender, (None, None))
        if ip:
            enqueue_message(sender, ip, port, pong)

    elif msg_type == "PONG":
        update_peer_heartbeat(sender)
        handle_pong(msg)

    elif msg_type == "INV":
        local = set(get_inventory())
        remote_ids = set(msg.get("blocks", []))
        missing = list(remote_ids - local)
        if missing:
            getmsg = create_getblock(self_id, missing)
            ip, port = known_peers.get(sender, (None, None))
            if ip:
                enqueue_message(sender, ip, port, getmsg)

    elif msg_type == "GETBLOCK":
        ids = msg.get("blocks", [])
        for bid in ids:
            blk = get_block_by_id(bid)
            attempts = 0
            while not blk and attempts < 3:
                req = create_getblock(self_id, [bid])
                for pid, (ip, port) in known_peers.items():
                    if pid in {self_id, sender}:
                        continue
                    enqueue_message(pid, ip, port, req)
                attempts += 1
                time.sleep(1)
                blk = get_block_by_id(bid)
            if not blk:
                continue
            ip, port = known_peers.get(sender, (None, None))
            if ip:
                if peer_flags.get(sender, {}).get("light"):
                    header = {"block_id": blk["block_id"], "prev_id": blk["prev_id"], "timestamp": blk["timestamp"]}
                    resp = {"type": "BLOCK_HEADERS", "sender": self_id, "headers": [header]}
                    enqueue_message(sender, ip, port, resp)
                else:
                    enqueue_message(sender, ip, port, blk)

    elif msg_type == "GET_BLOCK_HEADERS":
        headers = list(header_store)
        resp = {"type": "BLOCK_HEADERS", "sender": self_id, "headers": headers}
        ip, port = known_peers.get(sender, (None, None))
        if ip:
            enqueue_message(sender, ip, port, resp)

    elif msg_type == "BLOCK_HEADERS":
        incoming = msg.get("headers", [])
        local_ids = {b["block_id"] for b in received_blocks}
        known = {h["block_id"] for h in header_store} | local_ids
        valid = []
        for h in incoming:
            prev = h.get("prev_id")
            if prev is not None and prev not in known:
                return
            valid.append(h)
            known.add(h["block_id"])
        existing = {h["block_id"] for h in header_store}
        for h in valid:
            if h["block_id"] not in existing:
                header_store.append(h)
        if not peer_flags.get(self_id, {}).get("light"):
            missing = [h["block_id"] for h in valid if get_block_by_id(h["block_id"]) is None]
            if missing:
                req = create_getblock(self_id, missing)
                ip, port = known_peers.get(sender, (None, None))
                if ip:
                    enqueue_message(sender, ip, port, req)


    else:
        print(f"[{self_id}] Unknown message type: {msg_type}", flush=True)


def cleanup_seen_messages():
    now = time.time()
    expired = [msg_id for msg_id, ts in list(seen_message_ids.items()) if now - ts > SEEN_EXPIRY_SECONDS]
    for msg_id in expired:
        del seen_message_ids[msg_id]

