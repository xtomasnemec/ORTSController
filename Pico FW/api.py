import time
import config

try:
    import urequests as requests
except Exception:
    try:
        import requests
    except Exception:
        requests = None

try:
    import ujson as json
except Exception:
    import json

try:
    import network
except Exception:
    network = None

# module-level WLAN handle (set by connect_wifi)
_wlan = None


def get_json(url):
    if requests is None:
        raise RuntimeError("HTTP requests module is not available")
    response = requests.get(url)
    try:
        return response.json(), response.status_code
    finally:
        try:
            response.close()
        except Exception:
            pass

def connect_wifi():
    if network is None:
        return False

    global _wlan
    ssid = config.ssid
    password = config.password
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    while not wlan.isconnected():
        time.sleep(1)

    _wlan = wlan
    # local import to avoid circular import during module init
    try:
        from displaydriver import lcd_print as _lcd_print
        _lcd_print("WiFi:", ssid)
    except Exception:
        pass
    time.sleep(2)
    return True


def is_connected():
    try:
        return _wlan is not None and _wlan.isconnected()
    except Exception:
        return False

def test_connection():
    try:
        data, status = get_json(config.ip + "/APISAMPLE")
        if status == 200:
            try:
                from displaydriver import lcd_print as _lcd_print
                _lcd_print("TCP + OpenRails OK")
            except Exception:
                pass
        else:
            try:
                from displaydriver import lcd_print as _lcd_print
                _lcd_print("Spojeni nenavazano!")
            except Exception:
                pass
    except Exception as exc:
        try:
            from displaydriver import lcd_print as _lcd_print
            _lcd_print("Chyba pripojeni", str(exc))
        except Exception:
            pass
    time.sleep(2)


def _extract_body_text(html):
    start = html.find("<body>")
    end = html.find("</body>")
    if start == -1 or end == -1:
        return html.strip()
    return html[start + 6:end].strip()


def _format_clock_value(raw_value):
    value = float(raw_value)

    if value >= 864000000000:
        value = value % 864000000000
        total_seconds = int(value // 10000000)
    elif value >= 86400000:
        value = value % 86400000
        total_seconds = int(value // 1000)
    else:
        total_seconds = int(value) % 86400

    hours = (total_seconds // 3600) % 24
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)


def get_time():
    if requests is None:
        return "--:--:--"

    r = requests.get(config.ip + "/TIME")
    try:
        html = r.text
        return _format_clock_value(_extract_body_text(html))
    finally:
        try:
            r.close()
        except Exception:
            pass

def _get_hud_values():
    data, status = get_json(config.ip + "/HUD/0")

    table = data.get("commonTable") or {}
    values = table.get("values") or []
    return values


def _get_hud_field(field_name):
    values = _get_hud_values()

    for index in range(0, len(values) - 2, 3):
        label = values[index]
        value = values[index + 2]
        if label == field_name:
            return "" if value is None else str(value).strip()


def get_speed():
    return _get_hud_field("Speed")


def set_cab_control(type_name, value):
    root = str(config.ip).rstrip('/')

    tcp_host = config.server_tcp_host
    tcp_port = getattr(config, 'server_tcp_port', 5090)
    if tcp_host is None:
        try:
            tmp = root
            if tmp.startswith('http://'):
                tmp = tmp[7:]
            elif tmp.startswith('https://'):
                tmp = tmp[8:]
            hostpart = tmp.split('/')[0]
            host = hostpart.split(':')[0]
            if host:
                tcp_host = host
        except Exception:
            tcp_host = None

    if not tcp_host:
        raise RuntimeError("TCP control backend has no target host configured")

    try:
        import usocket as socket
    except Exception:
        try:
            import socket
        except Exception:
            socket = None

    if socket is None:
        raise RuntimeError("Socket module is not available")

    if getattr(config, 'DEBUG', False):
        print('set_cab_control: trying TCP', tcp_host, tcp_port, type_name, value)

    sock = socket.socket()
    try:
        sock.settimeout(1.5)
        sock.connect((tcp_host, int(tcp_port)))
        numeric_value = float(value)
        if numeric_value == int(numeric_value):
            value_text = str(int(numeric_value))
        else:
            value_text = str(numeric_value)
        line = str(type_name) + '=' + value_text + '\n'
        if getattr(config, 'DEBUG', False):
            print('set_cab_control: TCP send ->', line.strip())
        sock.send(line.encode('utf-8'))
        return 200
    finally:
        try:
            sock.close()
        except Exception:
            pass