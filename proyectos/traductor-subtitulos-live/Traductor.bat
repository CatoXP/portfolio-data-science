@echo off
REM Lanzador de doble clic: abre la app sin dejar una consola estorbando.
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
start "" pythonw main.py
