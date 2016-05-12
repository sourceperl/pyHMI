class Relay:
    def __init__(self):
        self.value = False
        self._value = False

    @property
    def state(self):
        """Get the current relay state."""
        return self.value

    @state.setter
    def state(self, new_state):
        self._value = self.value
        self.value = new_state

    @state.deleter
    def state(self):
        del self.value
        del self._value

    def trigger_pos(self):
        """True on positive edge."""
        return self.value and not self._value

    def trigger_neg(self):
        """True on negative edge."""
        return self._value and not self.value

    def toggle(self):
        """Toggle relay state."""
        self._value = self.value
        self.value = not self.value
