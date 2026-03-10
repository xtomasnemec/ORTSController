import ctypes
from ctypes import wintypes
import socketserver
import threading
import time
from pathlib import Path


LOG_PATH = Path(__file__).with_suffix(".log")

CONFIG = {
    "listen_host": "0.0.0.0",
    "listen_port": 5091,
    "window_title_contains": "Open Rails",
    "controls": {
        "HORN": {"mode": "hold", "key": "SPACE"},
        "BELL": {"mode": "hold", "key": "B"},
        "WHISTLE": {"mode": "hold", "key": "SPACE"},
        "LIGHT": {"mode": "tap", "key": "H"},
        "PANTOGRAPH1": {"mode": "tap", "key": "P"},
        "SANDER": {"mode": "hold", "key": "X"},
        "WIPERS": {"mode": "tap", "key": "V"},
        "ENABLE": {"mode": "noop"},
    },
}

VK_CODES = {
    "SPACE": 0x20,
    "B": 0x42,
    "H": 0x48,
    "P": 0x50,
    "V": 0x56,
    "X": 0x58,
}

INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
SW_RESTORE = 9


ULONG_PTR = wintypes.WPARAM


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _anonymous_ = ("union",)
    _fields_ = [("type", wintypes.DWORD), ("union", INPUT_UNION)]


def log(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write("[{}] {}\n".format(timestamp, message))


class KeyboardController:
    def __init__(self):
        self._pressed = set()
        self._lock = threading.Lock()
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
        self._user32.SendInput.restype = wintypes.UINT

    def _vk(self, key_name):
        key = str(key_name).upper()
        if key in VK_CODES:
            return VK_CODES[key]
        if len(key) == 1:
            return ord(key)
        raise KeyError("Unsupported key {}".format(key_name))

    def _scan_code(self, vk_code):
        return self._user32.MapVirtualKeyW(vk_code, 0)

    def _foreground_title(self):
        hwnd = self._user32.GetForegroundWindow()
        if not hwnd:
            return ""
        length = self._user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        self._user32.GetWindowTextW(hwnd, buffer, len(buffer))
        return buffer.value

    def _find_window(self, title_fragment):
        matches = []
        title_fragment = title_fragment.lower()

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def enum_proc(hwnd, _lparam):
            if not self._user32.IsWindowVisible(hwnd):
                return True
            length = self._user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buffer = ctypes.create_unicode_buffer(length + 1)
            self._user32.GetWindowTextW(hwnd, buffer, len(buffer))
            title = buffer.value.strip()
            if title_fragment in title.lower():
                matches.append((hwnd, title))
            return True

        self._user32.EnumWindows(enum_proc, 0)
        return matches[0] if matches else (None, "")

    def _focus_target_window(self):
        fragment = str(CONFIG.get("window_title_contains", "")).strip()
        if not fragment:
            return True

        hwnd, title = self._find_window(fragment)
        if not hwnd:
            log("OpenRails window not found; foreground='{}'".format(self._foreground_title()))
            return False

        foreground = self._user32.GetForegroundWindow()
        if foreground == hwnd:
            return True

        self._user32.ShowWindow(hwnd, SW_RESTORE)
        current_thread = self._kernel32.GetCurrentThreadId()
        foreground_thread = self._user32.GetWindowThreadProcessId(foreground, None)
        target_thread = self._user32.GetWindowThreadProcessId(hwnd, None)

        attached_foreground = False
        attached_target = False
        try:
            if foreground and foreground_thread and foreground_thread != current_thread:
                attached_foreground = bool(self._user32.AttachThreadInput(current_thread, foreground_thread, True))
            if target_thread and target_thread != current_thread:
                attached_target = bool(self._user32.AttachThreadInput(current_thread, target_thread, True))
            self._user32.BringWindowToTop(hwnd)
            self._user32.SetForegroundWindow(hwnd)
            self._user32.SetFocus(hwnd)
            self._user32.SetActiveWindow(hwnd)
        finally:
            if attached_target and target_thread and target_thread != current_thread:
                self._user32.AttachThreadInput(current_thread, target_thread, False)
            if attached_foreground and foreground_thread and foreground_thread != current_thread:
                self._user32.AttachThreadInput(current_thread, foreground_thread, False)

        focused = self._user32.GetForegroundWindow() == hwnd
        if not focused:
            log("failed to focus '{}' ; foreground='{}'".format(title, self._foreground_title()))
        return focused

    def _emit(self, vk_code, key_up=False):
        scan_code = self._scan_code(vk_code)
        flags = KEYEVENTF_SCANCODE
        if key_up:
            flags |= KEYEVENTF_KEYUP
        if vk_code in (0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E):
            flags |= KEYEVENTF_EXTENDEDKEY

        event = INPUT(
            type=INPUT_KEYBOARD,
            union=INPUT_UNION(
                ki=KEYBDINPUT(
                    wVk=0,
                    wScan=scan_code,
                    dwFlags=flags,
                    time=0,
                    dwExtraInfo=0,
                )
            ),
        )
        if self._user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT)) != 1:
            raise ctypes.WinError()

    def press(self, key_name):
        vk_code = self._vk(key_name)
        with self._lock:
            if vk_code in self._pressed:
                return
            self._focus_target_window()
            self._emit(vk_code, key_up=False)
            self._pressed.add(vk_code)
        log("key press {}".format(key_name))

    def release(self, key_name):
        vk_code = self._vk(key_name)
        with self._lock:
            if vk_code not in self._pressed:
                return
            self._focus_target_window()
            self._emit(vk_code, key_up=True)
            self._pressed.remove(vk_code)
        log("key release {}".format(key_name))

    def tap(self, key_name, hold_ms=60):
        self.press(key_name)
        time.sleep(hold_ms / 1000.0)
        self.release(key_name)

    def release_all(self):
        with self._lock:
            pressed = list(self._pressed)
            self._pressed.clear()
        for vk_code in pressed:
            try:
                self._focus_target_window()
                self._emit(vk_code, key_up=True)
            except Exception as exc:
                log("release_all error {}".format(exc))
        if pressed:
            log("released all keys")


class ControlRouter:
    def __init__(self, keyboard, controls):
        self.keyboard = keyboard
        self.controls = {name.upper(): value for name, value in controls.items()}

    @staticmethod
    def _is_pressed(value):
        try:
            return float(value) > 0.5
        except Exception:
            return str(value).strip().lower() in ("1", "true", "on")

    def apply(self, control_name, value):
        control = self.controls.get(control_name.upper())
        if not control:
            log("ignored unknown control {}={}".format(control_name, value))
            return

        mode = control.get("mode", "tap")
        key_name = control.get("key")
        pressed = self._is_pressed(value)

        if mode == "noop":
            log("noop control {}={}".format(control_name, value))
            return

        if not key_name:
            log("control {} missing key".format(control_name))
            return

        if mode == "hold":
            if pressed:
                self.keyboard.press(key_name)
            else:
                self.keyboard.release(key_name)
            return

        if mode == "tap":
            if pressed:
                self.keyboard.tap(key_name)
            return

        log("unsupported mode {} for {}".format(mode, control_name))


KEYBOARD = KeyboardController()
ROUTER = ControlRouter(KEYBOARD, CONFIG["controls"])


class TcpHandler(socketserver.StreamRequestHandler):
    def handle(self):
        peer = "{}:{}".format(*self.client_address)
        log("client connected {}".format(peer))
        try:
            while True:
                raw = self.rfile.readline()
                if not raw:
                    break
                line = raw.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                if "=" not in line:
                    log("ignored malformed line {}".format(line))
                    continue
                name, value = line.split("=", 1)
                log("control {}={}".format(name.strip(), value.strip()))
                ROUTER.apply(name.strip(), value.strip())
        except Exception as exc:
            log("client error {}: {}".format(peer, exc))
        finally:
            log("client disconnected {}".format(peer))


class ThreadedTcpServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    host = CONFIG["listen_host"]
    port = int(CONFIG["listen_port"])
    log("starting TCP responder on {}:{}".format(host, port))
    server = ThreadedTcpServer((host, port), TcpHandler)
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        KEYBOARD.release_all()
        server.server_close()
        log("server stopped")


if __name__ == "__main__":
    main()