$ErrorActionPreference = 'Stop'


$HostAddr = "localhost"
$DashPorts = 8000..8010


function Banner($msg) {
    Write-Host "";
    Write-Host $msg -ForegroundColor Cyan
}

Banner "1. Container status"
docker compose ps

Banner "2. Health check"
foreach ($port in $DashPorts) {
    $url = ('http://{0}:{1}/health' -f $HostAddr, $port)

    try {
        $resp = Invoke-WebRequest -Uri $url -UseBasicParsing
        $code = $resp.StatusCode
    } catch {
        if ($_.Exception.Response) { $code = $_.Exception.Response.StatusCode.value__ } else { $code = 0 }
    }
    Write-Host "port $port $code"
}

Banner "3. Known peers / tx pool / latest block"

$first = $DashPorts[0]
Invoke-WebRequest -Uri ('http://{0}:{1}/peers' -f $HostAddr, $first) -UseBasicParsing |


Banner "4. Submit valid transaction"
$body = @{ recipient="5001"; amount=42 } | ConvertTo-Json
$resp = Invoke-WebRequest -Uri ('http://{0}:{1}/transactions/new' -f $HostAddr, $first) -Method Post -Body $body -ContentType 'application/json' -UseBasicParsing
$txid = ($resp.Content | ConvertFrom-Json).id
Start-Sleep -Seconds 8
$blocks = Invoke-WebRequest -Uri ('http://{0}:{1}/blocks' -f $HostAddr, $first) -UseBasicParsing | Select-Object -ExpandProperty Content
if ($blocks -like "*$txid*") { Write-Host "✅ transaction on chain" }

Banner "5. Network metrics"
$r = Invoke-RestMethod -Uri ('http://{0}:{1}/latency' -f $HostAddr, $first)
$r.details.psobject.Properties | Select-Object Name,Value | Format-Table -AutoSize
Write-Host ("avg_ms=" + $r.avg_ms)
Invoke-RestMethod -Uri ('http://{0}:{1}/capacity' -f $HostAddr, $first) |
  Select-Object capacity | Format-Table -AutoSize


Banner "6. Blacklist demonstration"
for ($i=0; $i -lt 4; $i++) {
    $bad = @{ type="TX"; id="bad"; from="evil"; to="x"; amount=0 } | ConvertTo-Json
    Invoke-WebRequest -Uri ('http://{0}:{1}/transactions/new' -f $HostAddr, $first) -Method Post -Body $bad -ContentType 'application/json' -UseBasicParsing | Out-Null
}
Start-Sleep -Seconds 2
Invoke-WebRequest -Uri ('http://{0}:{1}/blacklist' -f $HostAddr, $first) -UseBasicParsing | Select-Object -ExpandProperty Content


Write-Host ""
Write-Host "Demo complete!" -ForegroundColor Green
