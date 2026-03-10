winget install -e --id Python.Python.3.11

cd "Pico FW"

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cd ..
call flash_python.bat
cd "Pico FW"

mpremote connect auto mip install github:brainelectronics/micropython-i2c-lcd
mpremote connect auto fs cp -r . :