@echo off
setlocal EnableExtensions EnableDelayedExpansion

winget install -e --id Python.Python.3.11

cd /d "%~dp0Pico FW"

if not exist ".venv\Scripts\python.exe" (
	py -3.11 -m venv .venv
)

set "PYTHON=.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
	echo Python virtual environment was not created successfully.
	exit /b 1
)

"%PYTHON%" -m pip install --upgrade pip
"%PYTHON%" -m pip install -r requirements.txt

set /a RETRIES=10

:wait_for_pico
"%PYTHON%" -m mpremote connect auto fs ls >nul 2>&1
if not errorlevel 1 goto pico_ready

set /a RETRIES-=1
if !RETRIES! LEQ 0 (
	echo mpremote: no device found.
	echo Make sure the Pico rebooted into MicroPython after flashing and is connected over USB data.
	exit /b 1
)

timeout /t 2 /nobreak >nul
goto wait_for_pico

:pico_ready
"%PYTHON%" -m mpremote connect auto mip install github:brainelectronics/micropython-i2c-lcd
if errorlevel 1 exit /b %errorlevel%

for %%F in (*.py) do (
	"%PYTHON%" -m mpremote connect auto fs cp "%%F" :"%%F"
	if errorlevel 1 exit /b !errorlevel!
)
"%PYTHON%" -m mpremote reset