from lcd_i2c import LCD
from machine import I2C, Pin

# nastavení sítě
ssid = "WIFI_NAME"
password = "WIFI_PASSWORD"

#ip adresa pocitace s openrails
ip = "http://192.168.1.100:2150/API/"

# Pokud tvůj OpenRails Web Server poskytuje přímo endpoint s hráčovým vlakem,
# nastav sem URL (např. ip + "playertrain" / "train/player" apod.).
# Když je None, použije se config.ip a hráčův vlak se najde heuristicky v JSONu.
player_train_url = None

#nastaveni displeje

NUM_ROWS = 4
NUM_COLS = 20

# PCF8574 on 0x50
I2C_ADDR = 0x27     # DEC 39, HEX 0x27

# define custom I2C interface, default is 'I2C(0)'
# check the docs of your device for further details and pin infos
i2c = I2C(0, scl=Pin(13), sda=Pin(12), freq=800000)
lcd = LCD(addr=I2C_ADDR, cols=NUM_COLS, rows=NUM_ROWS, i2c=i2c)