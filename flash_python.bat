@echo off
setlocal EnableExtensions
set "UF2=%~dp0RPI_PICO_W-20251209-v1.27.0.uf2"


for %%D in (D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    if exist %%D:\INFO_UF2.TXT (
        copy /Y "%UF2%" %%D:\ >nul
        exit /b 0
    )
)

echo "Nenasel jsem RPi Pico. Je v BOOTSEL modu???"
exit /b 1