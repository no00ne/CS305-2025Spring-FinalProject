@echo off
REM ==========================================================
REM  CS305-2025Spring-FinalProject  ——  全流程演示脚本 (CMD)
REM ==========================================================
setlocal enabledelayedexpansion

REM ---------- 全局配置 ----------
set HOST=localhost
set REST_OFFSET=1000          REM peerId+1000 = host REST
set DASH_OFFSET=3000          REM peerId+3000 = host Dashboard
set PEER_IDS=5000 5001 5002 5003 5004 5005 5006 5007 5008 5009 5010
set BLOCK_SLEEP=8             REM 区块时间间隔（秒）

REM ---------- 0. docker compose ps ----------
echo.
echo ========= docker compose ps =========
docker compose ps --format "table {{.Service}}\t{{.Publishers}}\t{{.Status}}"

REM ---------- 1. Health check ----------
echo.
echo ========= 1. Health check =========
for %%I in (%PEER_IDS%) do (
    set /a DPORT=%%I+%DASH_OFFSET%
    curl -s -o NUL -w "peer %%I  Dashboard !DPORT!  ->  %%{http_code}\n" ^
         http://%HOST%:!DPORT!/health
)

REM ---------- 2. Network status（只看第一个节点） ----------
for %%I in (%PEER_IDS%) do (
    set FIRST=%%I
    goto :next
)
:next
set /a REST_PORT=%FIRST%+%REST_OFFSET%
set /a DASH_PORT=%FIRST%+%DASH_OFFSET%

echo.
echo ========= 2. Peers / TX pool / Latest block =========
curl -s http://%HOST%:%DASH_PORT%/peers
echo ------------------------------
curl -s http://%HOST%:%DASH_PORT%/transactions
echo ------------------------------
curl -s http://%HOST%:%DASH_PORT%/blocks

REM ---------- 3. 提交合法交易 ----------
echo.
echo ========= 3. Submit valid transaction =========
FOR /F %%G IN ('powershell -NoProfile -Command "[guid]::NewGuid().ToString()"') DO set TXID=%%G
echo TXID=%TXID%

curl -s -H "Content-Type: application/json" ^
     -d "{\"id\":\"%TXID%\",\"from\":\"demo\",\"to\":\"demo\",\"amount\":1}" ^
     http://%HOST%:%REST_PORT%/transactions/new >NUL

echo Wait %BLOCK_SLEEP%s for new block...
timeout /t %BLOCK_SLEEP% >NUL

curl -s http://%HOST%:%REST_PORT%/blocks | findstr /I %TXID%
IF %ERRORLEVEL% EQU 0 (
    echo [OK] %TXID% on-chain.
) ELSE (
    echo [FAIL] %TXID% NOT found.
)

REM ---------- 4. Network metrics ----------
echo.
echo ========= 4. Network metrics =========
curl -s http://%HOST%:%DASH_PORT%/latency
echo ------------------------------
curl -s http://%HOST%:%DASH_PORT%/capacity

REM ---------- 5. Blacklist demonstration ----------
echo.
echo ========= 5. Blacklist demonstration =========
set BAD_JSON={"id":"dup","from":"x","to":"y","amount":-1}
curl -s -X POST -H "Content-Type: application/json" -d %BAD_JSON% ^
     http://%HOST%:%REST_PORT%/transactions/new >NUL
curl -s -X POST -H "Content-Type: application/json" -d %BAD_JSON% ^
     http://%HOST%:%REST_PORT%/transactions/new >NUL
timeout /t 3 >NUL
curl -s http://%HOST%:%REST_PORT%/blacklist

echo.
echo ========= Demo complete! =========
endlocal
