#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP Agent Simulator Control Plane: process lifecycle support
#


class AbstractGrowingValue(object):
    """Interface for computing how much a value has grown.
    """

    @property
    def latest(self):
        raise NotImplementedError()

    def added_content(self, relative_to=None):
        raise NotImplementedError()


class Gauge(AbstractGrowingValue, int):
    """Gauge integer number.

    Gauge objects can increase and decrease in value over time.
    """
    @property
    def latest(self):
        return 0

    def added_content(self, relative_to=None):
        return self

    def __add__(self, other):
        return Gauge(int(self) + other)

    def __sub__(self, other):
        return Gauge(int(self) - other)

    __iadd__ = __add__
    __isub__ = __sub__


class Counter(AbstractGrowingValue, int):
    """Integer counter.

    Counter object can only increase in value over time.
    """
    @property
    def latest(self):
        return self

    def added_content(self, relative_to=None):
        return max(0, self - (relative_to or 0))

    def __add__(self, other):
        return Counter(int(self) + other)

    __iadd__ = __add__


class ConsoleLog(AbstractGrowingValue):
    """Paged process console log.

    Text pages can be added at the end of the log, and automatically
    expire.
    """
    MAX_CONSOLES = 50
    MAX_CONSOLE_SIZE = 80 * 24  # tribute to VT100

    def __init__(self, first_page=0):
        self._first_page = first_page
        self._last_page = first_page
        self._text = {}
        self._timestamps = {}

    @property
    def first_page(self):
        return self._first_page

    @property
    def last_page(self):
        return self._last_page - 1

    def add(self, text, timestamp):
        self._text[self._last_page] = text
        self._timestamps[self._last_page] = timestamp
        self._last_page += 1

        if len(self._text) > self.MAX_CONSOLES:
            self._text.pop(self._first_page)
            self._timestamps.pop(self._first_page)
            self._first_page += 1

    def text(self, page):
        return self._text.get(page, '')

    def timestamp(self, page):
        return self._timestamps.get(page, '')

    @property
    def latest(self):
        return self.last_page

    def added_content(self, relative_to=None):
        first_page = relative_to or 0
        console = self.__class__(first_page=first_page)

        for page in range(first_page, self.last_page):
            console.add(self.text(page), self.timestamp(page))

        return console

