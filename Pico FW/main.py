import displaydriver as lcd
import api
import config
import buttons

lcd.init()

api.connect_wifi()
api.test_connection()

try:
	train = api.get_player_train()
	if isinstance(train, dict) and train:
		name = train.get("Name") or train.get("name") or train.get("DisplayName") or train.get("displayName")
		if name:
			lcd.simple_print("Vlak hrace:", str(name))
		else:
			lcd.simple_print("Vlak hrace OK")
	else:
		lcd.simple_print("Vlak hrace", "nenalezen")
except Exception as exc:
	lcd.simple_print("Chyba API", str(exc))