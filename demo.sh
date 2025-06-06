#!/bin/bash
# Demonstration script to showcase peer functionality.
# Run this after starting the containers with `docker compose up -d`.

ports=(8000 8001 8002 8003 8004 8005 8006 8007 8008 8009 8010)
containers=(peer5000 peer5001 peer5002 peer5003 peer5004 peer5005 peer5006 peer5007 peer5008 peer5009 peer5010)
endpoints=("" "peers" "blocks" "transactions" "latency" "capacity" "orphans" "queue" "redundancy" "blacklist")

# Show container status
echo "=== Container status ==="
docker compose ps

echo
for i in "${!containers[@]}"; do
    port="${ports[$i]}"
    c="${containers[$i]}"
    echo "===== $c (dashboard port $port) ====="
    echo "-- initialization logs --"
    docker logs "$c" 2>/dev/null | grep -E "Starting|Node is now running" | tail -n 10
    echo
    for ep in "${endpoints[@]}"; do
        url="http://localhost:${port}/${ep}"
        printf "GET %s\n" "$url"
        curl -s "$url"
        echo -e "\n"
    done
    echo
done

