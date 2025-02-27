# Copyright (c) 2024 - 2025 Kevin G. Schlosser

class Pin(object):
    IN = 0x00
    OUT = 0x01

    def __init__(self, id, mode=-1, value=None):  # NOQA
        self._id = id
        self._mode = 0
        self._buf = bytearray(2)
        self._mv = memoryview(self._buf)

        self.init(mode, value)

    def init(self, mode=-1, value=None):
        if mode != -1:
            self._set_dir(mode)
            self._mode = mode

        if value is not None:
            self._set_level(value)

    def value(self, x=None):
        if x is not None:
            self._set_level(x)
        else:
            return self._get_level()

    def __call__(self, x=None):
        if x is not None:
            self._set_level(x)
        else:
            return self._get_level()

    def off(self):
        self.value(0)

    def on(self):
        self.value(1)

    def low(self):
        self.value(0)

    def high(self):
        self.value(1)

    def mode(self, mode=None):
        if mode is None:
            return self._mode

        self.init(mode=mode)

    def _set_dir(self, direction):
        raise NotImplementedError

    def _set_level(self, level):
        raise NotImplementedError

    def _get_level(self):
        raise NotImplementedError
