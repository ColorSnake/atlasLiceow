@echo off
cd /d "%~dp0"
echo Atlas liceow: wymagany Node.js 22.13+ i zaleznosci npm ci.
echo Po pierwszym przygotowaniu lokalnej bazy uruchom adres pokazany przez serwer.
echo Aby zatrzymac serwer, nacisnij Ctrl+C.
call npm run dev -- --hostname 127.0.0.1
pause
