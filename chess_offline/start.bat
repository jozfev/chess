
@echo off
chcp 65001 > nul
title Chess Offline - Launcher

echo ================================
echo       CHESS OFFLINE
echo ================================
echo.

echo [1/2] Установка библиотек...
py -m pip install --upgrade pip
py -m pip install pygame-ce python-chess numpy

if errorlevel 1 (
    echo.
    echo Ошибка установки библиотек!
    pause
    exit /b 1
)

echo.
echo [2/2] Запуск шахмат...
py main.py

if errorlevel 1 (
    echo.
    echo Произошла ошибка при запуске!
    pause
)

pause
