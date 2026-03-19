@echo off
cd /d "%~dp0"

set "PY="
python --version >nul 2>&1
if %errorlevel% equ 0 ( set "PY=python" & goto :start )
py --version >nul 2>&1
if %errorlevel% equ 0 ( set "PY=py" & goto :start )
for %%V in (313 312 311 310 39) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set "PY=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" & goto :start
    )
)
echo Python nicht gefunden! & pause & exit /b 1

:start
:: Startet Python ohne CMD-Fenster (pythonw = kein Konsolenfenster)
set "PYW=%PY:python.exe=pythonw.exe%"
if exist "%PYW%" (
    start "" "%PYW%" preis_alarm.py
) else (
    :: Fallback: powershell versteckt das Fenster
    powershell -WindowStyle Hidden -Command "Start-Process '%PY%' -ArgumentList 'preis_alarm.py' -WorkingDirectory '%~dp0' -WindowStyle Hidden"
)
