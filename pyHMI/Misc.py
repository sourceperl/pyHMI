# -*- coding: utf-8 -*-


def limit(value, v_min, v_max):
    """
    limit a float or int python var

    :param value: value to limit
    :param v_min: minimum value
    :param v_max: maximum value
    :return: limited value
    """
    try:
        return min(max(value, v_min), v_max)
    except TypeError:
        return None


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
