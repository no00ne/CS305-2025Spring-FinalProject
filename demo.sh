
#!/usr/bin/env bash
# ===== CS305-2025Spring-FinalProject Demo =====
set -euo pipefail

HOST="localhost"
PEERS=(5000 5001 5002 5003 5004 5005 5006 5007 5008 5009 5010)
DASH_PORTS=(8000 8001 8002 8003 8004 8005 8006 8007 8008 8009 8010)

jq_exists(){ command -v jq >/dev/null 2>&1; }

banner(){ echo -e "\n\033[1;34m$*\033[0m"; }

banner "1. Container status"
docker compose ps

banner "2. Health check"
for port in "${DASH_PORTS[@]}"; do
  printf "port %-5s " "$port"
  code=$(curl -s -o /dev/null -w '%{http_code}' "http://${HOST}:${port}/health" || true)
  echo "$code"
done

banner "3. Known peers / tx pool / latest block"
first=${DASH_PORTS[0]}
curl -s "http://${HOST}:${first}/peers" | (jq_exists && jq '.' || cat)
curl -s "http://${HOST}:${first}/transactions" | (jq_exists && jq '.' || cat)
curl -s "http://${HOST}:${first}/blocks" | (jq_exists && jq '.[-1]' || cat)

banner "4. Submit valid transaction"
resp=$(curl -s -X POST "http://${HOST}:${first}/transactions/new" \
      -H "Content-Type: application/json" \
      -d '{"recipient":"5001","amount":42}')
if jq_exists; then
  txid=$(echo "$resp" | jq -r '.id')
else
  txid=$(echo "$resp" | sed -E 's/.*"id":"?([^"]+)"?.*/\1/')
fi
sleep 8
curl -s "http://${HOST}:${first}/blocks" | (jq_exists && jq '.[-1]' || cat) | grep -q "$txid" && echo "✅ transaction on chain"

banner "5. Network metrics"
curl -s "http://${HOST}:${first}/latency" | (jq_exists && jq '.' || cat)
curl -s "http://${HOST}:${first}/capacity" | (jq_exists && jq '.' || cat)

banner "6. Blacklist demonstration"
for i in {1..4}; do
  curl -s -X POST "http://${HOST}:${first}/transactions/new" \
       -H "Content-Type: application/json" \
       -d '{"id":"bad","recipient":"x","amount":0}' >/dev/null
done
sleep 2
curl -s "http://${HOST}:${first}/blacklist" | (jq_exists && jq '.' || cat)

echo -e "\n\033[1;32mDemo complete!\033[0m"


