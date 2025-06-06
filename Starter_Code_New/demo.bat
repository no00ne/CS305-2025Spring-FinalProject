@echo off
REM ================== CS305 Demo (UTF-8) ==================
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM -------- 全局配置 --------
set "HOST=localhost"

set "REST_OFFSET=3000"
set "DASH_OFFSET=3000"
set "PEERS=5000 5001 5002 5003 5004 5005 5006 5007 5008 5009 5010"

set "BLOCK_SLEEP=15"


REM -------- 工具检测 --------
where curl.exe >nul 2>&1 || (
   echo [ERROR] curl.exe 未找到，请检查 PATH
   exit /b 1
)
for %%C in (curl.exe) do set "CURL=%%~$PATH:C"

REM -------- 0. docker compose ps --------
echo.
echo ===== docker compose ps =====
docker compose ps --format "table {{.Service}}\t{{.Publishers}}\t{{.Status}}"

REM -------- 1. Health check --------
echo.
echo ===== 1. Health check =====
for %%I in (%PEERS%) do (
    set /a DPORT=%%I+%DASH_OFFSET%
    for /f %%H in ('^%CURL% -s -o nul -w ^%%{http_code^} "http://%HOST%:!DPORT!/health"') do (
        echo peer %%I  dashboard !DPORT!  ->  %%H
    )
)

REM -------- 2. 网络状态（取第 1 个节点） --------
for %%I in (%PEERS%) do (set FIRST=%%I & goto :afterLoop)
:afterLoop
set /a REST=%FIRST%+%REST_OFFSET%
set /a DASH=%FIRST%+%DASH_OFFSET%
set /a DASH2=%FIRST%+1+%DASH_OFFSET%

echo.
echo ==== 2. Peers / TX pool / Latest block ====

:: ---------- Peers ----------
echo [Peers]
%CURL% -s http://%HOST%:%REST%/peers

:: ---------- TX pool ----------
echo.
echo [TX Pool (top 10)]
%CURL% -s http://%HOST%:%REST%/transactions

:: ---------- Latest block ----------
echo.
echo [Latest Block (header only)]
%CURL% -s http://%HOST%:%REST%/blocks

echo.

REM -------- 3. 提交合法交易 --------
echo.
echo ===== 3. Submit valid transaction =====
for /f %%G in ('powershell -NoProfile -Command "[guid]::NewGuid()"') do set "TXID=%%G"
echo TXID=%TXID%

set "TXJSON={\"id\":\"%TXID%\",\"from\":\"demo\",\"to\":\"demo\",\"amount\":1}"
%CURL% -s -H "Content-Type: application/json" ^
       -d "%TXJSON%" ^
       http://%HOST%:%REST%/transactions/new >nul

echo 等待 %BLOCK_SLEEP% 秒打包区块…
powershell -NoProfile -Command "Start-Sleep -Seconds %BLOCK_SLEEP%"

for /f "delims=" %%B in ('%CURL% -s http://%HOST%:%REST%/blocks') do (
    echo %%B | findstr /I /C:"%TXID%" >nul && (
        echo [OK] %TXID% 已写入最新区块
        goto :latency
    )
)
echo [FAIL] %TXID% 未在最新区块中找到

:latency
REM -------- 4. Network metrics --------
echo.
echo ===== 4. Network metrics =====

powershell -NoProfile -Command "$r=Invoke-RestMethod http://%HOST%:%DASH%/latency;$r.details.psobject.Properties | Select-Object Name,Value | Format-Table -AutoSize; 'avg_ms='+$r.avg_ms"

echo ------------------------------
%CURL% -s http://%HOST%:%DASH%/capacity
powershell -NoProfile -Command "Invoke-RestMethod http://%HOST%:%DASH%/capacity | Select-Object capacity | Format-Table -AutoSize"

REM -------- 5. Orphan / Queue / Redundancy --------
echo.
echo ===== 5. Orphan / Queue / Redundancy =====
%CURL% -s http://%HOST%:%DASH%/orphan
%CURL% -s http://%HOST%:%DASH%/queue
%CURL% -s http://%HOST%:%DASH%/redundancy

REM -------- 6. Blacklist demonstration --------
echo.
echo ===== 6. Blacklist demonstration =====
set "BAD={\"type\":\"TX\",\"id\":\"dup\",\"from\":\"evil\",\"to\":\"y\",\"amount\":-1}"
set "TXURL=http://%HOST%:%REST%/transactions/new"
for /L %%N in (1,1,4) do %CURL% -s -X POST -H "Content-Type: application/json" -d "%BAD%" %TXURL% >nul
REM 等 3 秒让节点处理
powershell -NoProfile -Command "Start-Sleep -Seconds 3"
set "BLURL=http://%HOST%:%DASH2%/blacklist"
%CURL% -s %BLURL%

echo.
echo ===== Demo complete! =====
endlocal
