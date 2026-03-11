import time
import api
import config

try:
    import machine
except Exception:
    machine = None

if machine is None:
    import board
    import digitalio


def _make_button(pin_number):
    if pin_number is None:
        return None

    if machine is not None:
        return machine.Pin(pin_number, machine.Pin.IN, machine.Pin.PULL_UP)

    pin = digitalio.DigitalInOut(getattr(board, "GP{}".format(pin_number)))
    pin.direction = digitalio.Direction.INPUT
    pin.pull = digitalio.Pull.UP
    return pin


def _read_button(button):
    if button is None:
        return 1

    value = button.value
    if callable(value):
        value = value()
    return 1 if value else 0

# active-low buttons
horn_button = _make_button(getattr(config, "HORN_PIN", 1))
bell_button = _make_button(getattr(config, "BELL_PIN", 2))
enable_button = _make_button(getattr(config, "ENABLE_PIN", None))

# debounce timing
DEBOUNCE_MS = 20

_buttons = {}


def _ticks_ms():
    return time.ticks_ms()


def _make_state(name, button, pulse_only=False):
    raw = _read_button(button)
    return {
        "name": name,
        "button": button,
        "pulse_only": pulse_only,
        "stable": raw,
        "last_raw": raw,
        "changed_at": _ticks_ms(),
    }


def _debug_button(message, *parts):
    if config.DEBUG:
        print(message, *parts)

def init():
    """Initialize button module state. Call once before using poll()."""
    global _buttons
    _buttons = {
        "HORN": _make_state("HORN", horn_button),
        "BELL": _make_state("BELL", bell_button, pulse_only=True),
        "ENABLE": _make_state("ENABLE", enable_button, pulse_only=True),
    }

    horn_state = _buttons["HORN"]["stable"]
    try:
        status = api.set_cab_control("HORN", 0.0 if horn_state else 1.0)
        if config.DEBUG:
            print("Initial HORN API status:", status)
    except Exception as e:
        if config.DEBUG:
            print("Initial HORN API error:", e)
    if config.DEBUG:
        print("buttons.init: GPIO{} state=".format(getattr(config, "HORN_PIN", 1)), "pressed" if not horn_state else "released")


def _handle_edge(state, now):
    current_state = state["stable"]
    name = state["name"]
    try:
        value = 1.0 if not current_state else 0.0
        if state["pulse_only"] and value == 0.0:
            return True
        status = api.set_cab_control(name, value)
        _debug_button(
            "buttons.poll:",
            name,
            "->",
            "pressed" if not current_state else "released",
            "at",
            now,
            "api_status:",
            status,
        )
    except Exception as e:
        _debug_button(name, "API error:", e)
    return True


def poll():
    if not _buttons:
        init()

    now = _ticks_ms()
    handled = False

    for button_state in _buttons.values():
        button = button_state["button"]
        if button is None:
            continue

        raw = _read_button(button)
        if raw != button_state["last_raw"]:
            button_state["last_raw"] = raw
            button_state["changed_at"] = now
            _debug_button(
                "buttons.raw:",
                button_state["name"],
                "GPIO{}".format(getattr(config, button_state["name"] + "_PIN", "?")),
                "->",
                "pressed" if not raw else "released",
            )
            continue

        if raw != button_state["stable"] and time.ticks_diff(now, button_state["changed_at"]) >= DEBOUNCE_MS:
            button_state["stable"] = raw
            handled = _handle_edge(button_state, now) or handled

    return handled


def main():
    while True:
        if config.DEBUG:
            # show poll heartbeat when debugging
            changed = poll()
            if changed:
                print("buttons.main: poll handled a change")
        else:
            poll()
        time.sleep_ms(getattr(config, "BUTTON_POLL_MS", 10))