@echo off
chcp 65001 > nul
title PDF Douanes — Arret

echo  Arret de l'application...
docker-compose down
echo  ✓ Application arretee.
pause
