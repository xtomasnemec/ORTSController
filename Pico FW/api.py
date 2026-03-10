import urequests as requests
import network
import time
import config
import displaydriver as lcd


def get_json(url):
    response = requests.get(url)
    try:
        return response.json(), response.status_code
    finally:
        try:
            response.close()
        except Exception:
            pass

def connect_wifi():
    ssid = config.ssid
    password = config.password
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    while not wlan.isconnected():
        time.sleep(1)

    lcd.simple_print("Pripojeno:", ssid)
    time.sleep(2)

def test_connection():
    try:
        status = get_json(config.ip)
        if status == 200:
            lcd.simple_print("Spojeno s OpenRails")
        else:
            lcd.simple_print("Spojeni nenavazano!")
    except Exception as exc:
        lcd.simple_print("Chyba pripojeni", str(exc))
    time.sleep(2)