"""A tiny shopping cart — the demo project for the coding-agent tutorial.

Exactly one bug lives here on purpose: Cart.add() replaces the quantity
when the same item is added twice instead of accumulating it.
"""


class Cart:
    def __init__(self):
        self._items = {}  # name -> [unit_price_cents, quantity]

    def add(self, name, unit_price_cents, quantity=1):
        # BUG (planted): this replaces the quantity instead of adding to it.
        self._items[name] = [unit_price_cents, quantity]

    def remove(self, name):
        self._items.pop(name, None)

    def quantity(self, name):
        entry = self._items.get(name)
        return entry[1] if entry else 0

    def total_cents(self):
        return sum(price * qty for price, qty in self._items.values())
