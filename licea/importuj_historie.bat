@echo off
cd /d "%~dp0"
python scripts\datasets.py import-batch imports\historical-batch.json
if errorlevel 1 exit /b 1
echo Import zakonczony. Odswiez lokalna aplikacje. Publikacja internetowa jest osobnym krokiem.
