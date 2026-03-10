import config

def init():
    lcd = config.lcd

    lcd.begin()
    lcd.display()
    lcd.backlight()
    lcd.no_blink()
    simple_print("ORTSController")

def simple_print(*lines):
    lcd = config.lcd
    lcd.clear()
    if not lines:
        return
    text_lines = [str(x) for x in lines if x is not None]
    # Většina lcd_i2c driverů podporuje '\n' jako nový řádek.
    joined = "\n".join(s[: config.NUM_COLS] for s in text_lines[: config.NUM_ROWS])
    lcd.print(joined)

def main_screen():
    config.lcd.clear()