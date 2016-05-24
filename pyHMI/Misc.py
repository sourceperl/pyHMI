# -*- coding: utf-8 -*-


class Relay:
    def __init__(self):
        self._value = False
        self._last_value = False

    def update(self, state):
        """Set the current relay state."""
        self._last_value = self._value
        self._value = state

    @property
    def state(self):
        """Get the current relay state."""
        return self._value

    def trigger_pos(self):
        """True on positive edge."""
        return self._value and not self._last_value

    def trigger_neg(self):
        """True on negative edge."""
        return self._last_value and not self._value

    def toggle(self):
        """Toggle relay state."""
        self.update(not self._value)
