$ErrorActionPreference = 'Stop'

$HOST = "localhost"
$DASH_PORTS = 8000..8010

function Banner($msg) {
    Write-Host "";
    Write-Host $msg -ForegroundColor Cyan
}

Banner "1. Container status"
docker compose ps

Banner "2. Health check"
foreach ($port in $DASH_PORTS) {
    $url = "http://${HOST}:$port/health"
    try {
        $resp = Invoke-WebRequest -Uri $url -UseBasicParsing
        $code = $resp.StatusCode
    } catch {
        if ($_.Exception.Response) { $code = $_.Exception.Response.StatusCode.value__ } else { $code = 0 }
    }
    Write-Host "port $port $code"
}

Banner "3. Known peers / tx pool / latest block"
$first = $DASH_PORTS[0]
Invoke-WebRequest -Uri "http://${HOST}:$first/peers" -UseBasicParsing | Select-Object -ExpandProperty Content
Invoke-WebRequest -Uri "http://${HOST}:$first/transactions" -UseBasicParsing | Select-Object -ExpandProperty Content
$latest = Invoke-WebRequest -Uri "http://${HOST}:$first/blocks" -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json | Select -Last 1 | ConvertTo-Json -Depth 5
Write-Host $latest

Banner "4. Submit valid transaction"
$body = @{ recipient="5001"; amount=42 } | ConvertTo-Json
$resp = Invoke-WebRequest -Uri "http://${HOST}:$first/transactions/new" -Method Post -Body $body -ContentType "application/json" -UseBasicParsing
$txid = ($resp.Content | ConvertFrom-Json).id
Start-Sleep -Seconds 8
$blocks = Invoke-WebRequest -Uri "http://${HOST}:$first/blocks" -UseBasicParsing | Select-Object -ExpandProperty Content
if ($blocks -like "*$txid*") { Write-Host "✅ transaction on chain" }

Banner "5. Network metrics"
Invoke-WebRequest -Uri "http://${HOST}:$first/latency" -UseBasicParsing | Select-Object -ExpandProperty Content
Invoke-WebRequest -Uri "http://${HOST}:$first/capacity" -UseBasicParsing | Select-Object -ExpandProperty Content

Banner "6. Blacklist demonstration"
for ($i=0; $i -lt 4; $i++) {
    $bad = @{ id="bad"; recipient="x"; amount=0 } | ConvertTo-Json
    Invoke-WebRequest -Uri "http://${HOST}:$first/transactions/new" -Method Post -Body $bad -ContentType "application/json" -UseBasicParsing | Out-Null
}
Start-Sleep -Seconds 2
Invoke-WebRequest -Uri "http://${HOST}:$first/blacklist" -UseBasicParsing | Select-Object -ExpandProperty Content

Write-Host ""
Write-Host "Demo complete!" -ForegroundColor Green
