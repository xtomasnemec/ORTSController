from lcd_i2c import LCD
from machine import I2C, Pin

# nastavení sítě
ssid = "havroshAPK"
password = "klokaN-147*321xx"

#ip adresa pocitace s openrails
ip = "http://192.168.30.108:2150/API/"

CONTROL_BACKEND = "tcp"

player_train_url = None

# TCP responder host/port for button control. If host is left None, it will be
# derived from the OpenRails HTTP URL.
server_tcp_host = None
server_tcp_port = 5091

DEBUG = True

BUTTON_POLL_MS = 10
DISPLAY_REFRESH_MS = 50

HORN_PIN = 1
BELL_PIN = 2
ENABLE_PIN = 3

#nastaveni displeje

NUM_ROWS = 4
NUM_COLS = 20

# Bezna adresa PCF8574 backpacku je 0x27 nebo 0x3F.
I2C_ADDR = 0x27
I2C_FALLBACK_ADDRS = (0x27, 0x3F)
I2C_FREQ = 100000

# define custom I2C interface, default is 'I2C(0)'
# check the docs of your device for further details and pin infos
if LCD is not None and I2C is not None and Pin is not None:
	i2c = I2C(0, scl=Pin(13), sda=Pin(12), freq=I2C_FREQ)
	lcd = LCD(addr=I2C_ADDR, cols=NUM_COLS, rows=NUM_ROWS, i2c=i2c)
else:
	i2c = None
	lcd = None