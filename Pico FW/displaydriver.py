from lcd_i2c import LCD
from machine import I2C, Pin

def init():
    I2C_ADDR = config.I2C_ADDR
    NUM_ROWS = 4
    NUM_COLS = 20

    i2c = config.i2c
    lcd = config.lcd

    lcd.begin()
    lcd.display()
    lcd.backlight()
    lcd.no_blink()
    lcd.print("Hello World")

def simple_print(text):
    lcd.clear()
    lcd.print(text)

def main_screen():
    lcd.clear()