"""Suite for the demo cart: 4 tests, exactly 1 failing (the planted bug).

Runs under pytest AND under python -m unittest.
"""

import unittest

from cart import Cart


class TestCart(unittest.TestCase):
    def test_add_new_item(self):
        cart = Cart()
        cart.add("notebook", 499, 2)
        self.assertEqual(cart.quantity("notebook"), 2)

    def test_add_same_item_twice_accumulates(self):
        cart = Cart()
        cart.add("notebook", 499, 2)
        cart.add("notebook", 499, 3)
        self.assertEqual(cart.quantity("notebook"), 5)  # FAILS on the planted bug (gets 3)

    def test_total_cents(self):
        cart = Cart()
        cart.add("notebook", 499, 2)
        cart.add("pen", 150, 1)
        self.assertEqual(cart.total_cents(), 499 * 2 + 150)

    def test_remove_item(self):
        cart = Cart()
        cart.add("pen", 150, 1)
        cart.remove("pen")
        self.assertEqual(cart.quantity("pen"), 0)


if __name__ == "__main__":
    unittest.main()
