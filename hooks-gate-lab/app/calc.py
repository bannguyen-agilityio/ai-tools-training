def add(a, b):
    return a + b


def apply_discount(price, percent):
    """Return the price after a percent discount.

    BUG (on purpose, for Exercise 3): the discount is applied twice.
    """
    return price - price * percent / 100 * 2
