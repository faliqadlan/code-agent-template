import unittest

from app import add


class AddTests(unittest.TestCase):
    def test_adds_two_values(self) -> None:
        self.assertEqual(5, add(2, 3))


if __name__ == "__main__":
    unittest.main()
