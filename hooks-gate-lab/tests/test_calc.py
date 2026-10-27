import unittest

from app.calc import add, apply_discount


class TestCalc(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)

    def test_apply_discount(self):
        self.assertEqual(apply_discount(100, 10), 90)


if __name__ == "__main__":
    unittest.main()
