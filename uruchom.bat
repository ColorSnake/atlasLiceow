@echo off
cd /d "%~dp0"
echo Atlas liceow: otworz http://127.0.0.1:8765/ w przegladarce.
echo Aby zatrzymac serwer, nacisnij Ctrl+C.
python -m http.server 8765 --bind 127.0.0.1 --directory dist
pause
