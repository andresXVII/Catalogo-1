@echo off
cd /d "%~dp0"
title Catalogo de productos - Lanzador

netstat -ano | findstr /r /c:":8000 .*LISTENING" >nul
if %errorlevel%==0 (
  start "" "http://localhost:8000"
  exit /b
)

start "Servidor Catalogo" cmd /k py run.py
timeout /t 2 /nobreak >nul
start "" "http://localhost:8000"
