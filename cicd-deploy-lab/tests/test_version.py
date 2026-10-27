import unittest

from app.version import VERSION, health, parse_version


class VersionTests(unittest.TestCase):
    def test_health(self):
        self.assertEqual(health(), {"status": "ok", "version": VERSION})

    def test_parse(self):
        self.assertEqual(parse_version("1.2.3"), (1, 2, 3))

    def test_parse_bad(self):
        with self.assertRaises(ValueError):
            parse_version("1.2")


if __name__ == "__main__":
    unittest.main()
