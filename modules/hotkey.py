# Global hotkey listener using the Windows RegisterHotKey API (no extra dependencies).

import ctypes
import ctypes.wintypes
import threading

_WM_HOTKEY    = 0x0312
_WM_QUIT      = 0x0012
_MOD_NOREPEAT = 0x4000

_VK = {c: ord(c.upper()) for c in "abcdefghijklmnopqrstuvwxyz"}
_VK.update({str(d): 0x30 + d for d in range(10)})


# Registers a single global hotkey and calls callback() when pressed.
class HotkeyManager:
    def __init__(self, callback) -> None:
        self._callback   = callback
        self._thread: threading.Thread | None = None
        self._thread_id: int | None = None
        self._vk         = 0
        self._id         = 1

    # Registers a new hotkey key (single letter a-z or digit 0-9). Returns True on success.
    def set_key(self, key: str) -> bool:
        self.stop()
        vk = _VK.get(key.lower()) if key else 0
        if not vk:
            return False
        self._vk     = vk
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return True

    # Unregisters the current hotkey and stops the listener thread.
    def stop(self) -> None:
        if self._thread and self._thread.is_alive():
            if self._thread_id:
                ctypes.windll.user32.PostThreadMessageW(
                    self._thread_id, _WM_QUIT, 0, 0
                )
            self._thread.join(timeout=1.0)
        self._thread    = None
        self._thread_id = None

    def _run(self) -> None:
        self._thread_id = threading.get_ident()
        ok = ctypes.windll.user32.RegisterHotKey(None, self._id, _MOD_NOREPEAT, self._vk)
        if not ok:
            return
        try:
            msg = ctypes.wintypes.MSG()
            while True:
                ret = ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if ret <= 0:
                    break
                if msg.message == _WM_HOTKEY and msg.wParam == self._id:
                    self._callback()
        finally:
            ctypes.windll.user32.UnregisterHotKey(None, self._id)