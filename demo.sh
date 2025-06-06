#!/bin/bash
# Demonstration script to query each peer's dashboard endpoints

ports=(8000 8001 8002 8003 8004 8005 8006 8007 8008 8009 8010)
endpoints=("" "peers" "blocks" "transactions" "latency" "capacity" "orphans" "queue" "redundancy" "blacklist")

for port in "${ports[@]}"; do
    echo "===== Peer dashboard on port $port ====="
    for ep in "${endpoints[@]}"; do
        url="http://localhost:${port}/${ep}"
        echo "-- GET ${url}"
        curl -s "$url"
        echo -e "\n"
    done
    echo
done

