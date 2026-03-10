import displaydriver as lcd
import api
import config
import buttons
import time


lcd.init()
lcd.lcd_print("   ORTSController")

api.connect_wifi()
api.test_connection()

buttons.init()

last_display_ms = time.ticks_ms()

while True:
	try:
		buttons.poll()
	except Exception as e:
		print("Buttons poll error:", e)

	try:
		now = time.ticks_ms()
		if api.is_connected() and time.ticks_diff(now, last_display_ms) >= getattr(config, "DISPLAY_REFRESH_MS", 500):
			lcd.ORTSscreen()
			last_display_ms = now
		else:
			if not api.is_connected() and time.ticks_diff(now, last_display_ms) >= getattr(config, "DISPLAY_REFRESH_MS", 500):
				lcd.lcd_print("No WiFi", "Connecting...")
				last_display_ms = now
	except Exception as e:
		print("LCD error:", e)

	# keep display responsive but don't starve button polling
	time.sleep_ms(getattr(config, "BUTTON_POLL_MS", 10))