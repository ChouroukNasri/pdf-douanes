@echo off
chcp 65001 > nul
title PDF Douanes — Mise a jour

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   🔄 Mise a jour PDF Douanes                  ║
echo  ╚══════════════════════════════════════════════╝
echo.

echo  Recuperation de la derniere version...
git pull
if %errorlevel% neq 0 (
    echo  ✗ Erreur git pull. Verifiez votre connexion internet.
    pause
    exit /b 1
)

echo  Reconstruction de l'application...
docker-compose up -d --build
if %errorlevel% neq 0 (
    echo  ✗ Erreur Docker. Verifiez que Docker Desktop est ouvert.
    pause
    exit /b 1
)

echo.
echo  ✅ Mise a jour terminee !
timeout /t 3 > nul
start "" "http://localhost:8501"
pause
