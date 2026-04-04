@echo off
chcp 65001 > nul
title PDF Douanes — Docker

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   📑 PDF Douanes — Lancement Docker           ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: Verifier Docker
docker --version > nul 2>&1
if %errorlevel% neq 0 (
    echo  ✗ Docker non installe !
    echo.
    echo  Telechargez Docker Desktop :
    echo  https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)
echo  ✓ Docker detecte

:: Verifier si le container tourne deja
docker ps | findstr "pdf_douanes" > nul 2>&1
if %errorlevel% == 0 (
    echo  ✓ Application deja en cours...
    echo.
    echo  Ouverture du navigateur...
    start "" "http://localhost:8501"
    pause
    exit /b 0
)

echo.
echo  Demarrage de l'application...
echo  (Premiere fois : 2-3 minutes pour construire l'image)
echo.

docker-compose up -d

if %errorlevel% neq 0 (
    echo.
    echo  ✗ Erreur au demarrage. Verifiez que Docker Desktop est ouvert.
    pause
    exit /b 1
)

echo.
echo  ✓ Application demarree !
echo.
timeout /t 3 > nul
start "" "http://localhost:8501"

echo  Adresse : http://localhost:8501
echo.
echo  Pour arreter l'application : lancez ARRETER_DOCKER.bat
echo.
pause
