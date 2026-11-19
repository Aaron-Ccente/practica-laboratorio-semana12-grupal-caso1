@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
 echo Primero ejecuta los comandos del README para crear .venv e instalar Django.
 pause
 exit /b 1
)
.venv\Scripts\python.exe manage.py runserver
pause
2