import config
from lcd_i2c import LCD
import api
import time


def _format_i2c_addresses(addresses):
    return ", ".join("0x{:02X}".format(addr) for addr in addresses)


def init():
    if config.lcd is None or config.i2c is None:
        return

    addresses = config.i2c.scan()

    if config.I2C_ADDR not in addresses:
        fallback = next((addr for addr in config.I2C_FALLBACK_ADDRS if addr in addresses), None)

    lcd = config.lcd

    lcd.begin()
    lcd.display()
    lcd.backlight()
    lcd.no_blink()

def lcd_print(*lines):
    lcd = config.lcd
    if lcd is None:
        return
    lcd.clear()
    if not lines:
        return
    text_lines = [str(x) for x in lines if x is not None]
    for row, text in enumerate(text_lines[: config.NUM_ROWS]):
        lcd.set_cursor(col=0, row=row)
        s = text[: config.NUM_COLS]
        if len(s) < config.NUM_COLS:
            s = s + (" " * (config.NUM_COLS - len(s)))
        lcd.print(s)

def ORTSscreen():
    lcd_print(
        "    Cas: " + api.get_time(),
        "Rychlost: " + api.get_speed(),
    )

# compatibility alias: some modules expect `simple_print`
simple_print = lcd_print


def display_json(json_text):
    try:
        import ujson
        data = ujson.loads(json_text)
    except Exception as e:
        try:
            simple_print("JSON parse error", str(e))
        except Exception:
            pass
        return

    try:
        intd = data.get('intData', '')
        strd = data.get('strData', '')
        dated = data.get('dateData', '')
        embedded = data.get('embedded', {}) or {}
        embstr = embedded.get('Str', '')
        arr = data.get('strArrayData', []) or []
        first = arr[0] if arr else ''

        # Prepare up to NUM_ROWS lines
        lines = [
            "Int: {}".format(intd),
            str(strd)[: config.NUM_COLS],
            ("Emb: " + str(embstr))[: config.NUM_COLS],
            str(first)[: config.NUM_COLS],
        ]

        simple_print(*lines[: config.NUM_ROWS])
    except Exception as e:
        try:
            simple_print("Display error", str(e))
        except Exception:
            pass