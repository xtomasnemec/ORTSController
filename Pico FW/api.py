import urequests as requests
import network
import time
import config
import displaydriver as lcd

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
        response = requests.get(config.ip)
        if response.status_code == 200:
            lcd.simple_print("Spojeno s OpenRails")
        else:
            lcd.simple_print("Spojeni nenavazano!")
    time.sleep(2)